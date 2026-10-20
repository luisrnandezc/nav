/* FPT calendar: existing Django actions, no scheduling or UI dependencies. */
(() => {
    'use strict';
    const config = JSON.parse(document.getElementById('fpt-config').textContent);
    const $ = id => document.getElementById(id);
    const url = (name, id) => config.urls[name].replace('/0/', `/${id}/`);
    const hourLabel = hour => `${String(hour).padStart(2, '0')}:00`;
    const dateLabel = value => new Date(`${value}T12:00:00`).toLocaleDateString('es-VE', { day: '2-digit', month: 'short', year: 'numeric' });
    const periodLabel = period => `${dateLabel(period.start_date)} → ${dateLabel(period.end_date)} · ${period.is_active ? 'Abierto' : 'Cerrado'}`;
    const state = { periods: [], current: null, detail: null, participants: null, session: null, editingPeriod: null, load: 0 };
    const fieldLabels = { period: 'Periodo', date: 'Fecha', start_hour: 'Hora de inicio', status: 'Estado', student: 'Estudiante', instructor: 'Instructor', category: 'Categoría', start_date: 'Inicio', end_date: 'Cierre' };

    function message(id, text = '', error = false) {
        $(id).textContent = text;
        $(id).hidden = !text;
        $(id).classList.toggle('fpt-error', error);
    }

    async function request(endpoint, data) {
        const options = { credentials: 'same-origin', headers: { Accept: 'application/json' } };
        if (data !== undefined) {
            options.method = 'POST';
            options.headers['Content-Type'] = 'application/json';
            options.headers['X-CSRFToken'] = document.querySelector('[name=csrfmiddlewaretoken]').value;
            options.body = JSON.stringify(data);
        }
        let response;
        try { response = await fetch(endpoint, options); }
        catch { throw new Error('No se pudo conectar. Revise su conexión e intente de nuevo.'); }
        if (response.redirected || !response.headers.get('content-type')?.includes('application/json')) {
            throw new Error('No se pudo cargar la respuesta. Su sesión puede haber vencido; vuelva a iniciar sesión.');
        }
        const result = await response.json();
        if (!response.ok) {
            const details = Object.entries(result.errors || {}).flatMap(([field, errors]) =>
                errors.map(error => `${fieldLabels[field] ? `${fieldLabels[field]}: ` : ''}${error}`));
            const error = new Error(details.length ? details.join('\n') : result.error || 'No se pudo completar la operación.');
            error.status = response.status;
            error.code = result.code;
            throw error;
        }
        return result;
    }

    function fillSelect(select, choices, selected) {
        select.replaceChildren(...choices.map(([value, label]) => new Option(label, value)));
        if (selected !== undefined && selected !== null) select.value = String(selected);
    }

    async function refresh(preferred = state.current) {
        const generation = ++state.load;
        $('calendar-grid').setAttribute('aria-busy', 'true');
        $('refresh-calendar').disabled = true;
        $('calendar-grid').replaceChildren(Object.assign(document.createElement('p'), { className: 'ui-empty', textContent: 'Cargando calendario…' }));
        state.detail = null;
        try {
            const data = await request(url('periods'));
            if (generation !== state.load) return;
            // Chronological navigation; prefer the open period containing today.
            state.periods = data.periods.slice().sort((a, b) => a.start_date.localeCompare(b.start_date));
            const today = localDate(new Date());
            const selected = state.periods.find(p => p.id === Number(preferred))
                || state.periods.find(p => p.is_active && p.start_date <= today && today <= p.end_date)
                || state.periods.find(p => p.is_active) || state.periods.at(-1);
            state.current = selected?.id ?? null;
            fillSelect($('period-select'), state.periods.map(p => [p.id, periodLabel(p)]), state.current);
            $('period-select').disabled = !selected;
            if (!selected) fillSelect($('period-select'), [['', 'Sin periodos disponibles']]);
            const index = state.periods.indexOf(selected);
            $('previous-period').disabled = !selected || index === 0;
            $('next-period').disabled = !selected || index === state.periods.length - 1;
            $('period-state').hidden = !selected;
            if (config.canManage) {
                $('edit-period').hidden = !selected;
                fillSelect($('session-category'), [['', 'Seleccione una categoría'], ...data.categories.map(c => [c.value, `${c.value} — ${c.label}`])], $('session-category').value);
            }
            if (!selected) {
                $('calendar-grid').replaceChildren(Object.assign(document.createElement('p'), { className: 'ui-empty', textContent: config.canManage ? 'No hay periodos FPT. Crea un nuevo periodo para comenzar.' : 'No hay periodos FPT disponibles.' }));
                return true;
            }
            const detail = await request(url('period', selected.id));
            if (generation !== state.load) return;
            state.detail = detail;
            $('period-state').textContent = detail.period.is_active ? 'Abierto' : 'Cerrado';
            $('period-state').className = `badge ${detail.period.is_active ? 'badge-green' : 'badge-gray'}`;
            renderGrid(detail);
            return true;
        } catch (error) {
            if (generation !== state.load) return;
            message('page-message', error.message, true);
            $('calendar-grid').replaceChildren(Object.assign(document.createElement('p'), { className: 'ui-empty', textContent: 'No se pudo cargar el calendario. Pulsa Actualizar para reintentar.' }));
            return false;
        } finally {
            if (generation === state.load) {
                $('calendar-grid').setAttribute('aria-busy', 'false');
                $('refresh-calendar').disabled = false;
            }
        }
    }

    function renderGrid(detail) {
        const fragment = document.createDocumentFragment();
        for (let offset = 0; offset < detail.days.length; offset += 7) {
            const days = detail.days.slice(offset, offset + 7);
            const columns = [...days, ...Array(7 - days.length).fill(null)];
            const wrapper = document.createElement('div');
            wrapper.className = 'fpt-week';
            wrapper.tabIndex = 0;
            wrapper.setAttribute('role', 'region');
            wrapper.setAttribute('aria-label', `Calendario desde ${dateLabel(days[0].date)}; desplaza horizontalmente para ver todos los días`);
            const table = document.createElement('table');
            table.className = 'fpt-table';
            const caption = table.createCaption();
            caption.textContent = `${dateLabel(days[0].date)} → ${dateLabel(days.at(-1).date)}`;
            const header = table.createTHead().insertRow();
            const corner = document.createElement('th'); corner.textContent = 'Hora'; corner.scope = 'col'; header.append(corner);
            columns.forEach(day => {
                const th = document.createElement('th'); th.scope = 'col';
                if (day) th.textContent = new Date(`${day.date}T12:00:00`).toLocaleDateString('es-VE', { weekday: 'short', day: '2-digit', month: 'short' });
                else th.setAttribute('aria-hidden', 'true');
                header.append(th);
            });
            const body = table.createTBody();
            for (let hour = 8; hour <= 19; hour++) {
                const row = body.insertRow();
                const th = document.createElement('th'); th.scope = 'row'; th.className = 'fpt-hour'; th.textContent = hourLabel(hour); row.append(th);
                columns.forEach(day => {
                    const cell = row.insertCell();
                    if (!day) { cell.setAttribute('aria-hidden', 'true'); return; }
                    const session = detail.sessions.find(s => s.date === day.date && s.start_hour <= hour && hour < s.start_hour + 2);
                    const available = hour <= 18 && day.available_start_hours.includes(hour);
                    const clickable = Boolean(session || (available && config.canManage));
                    const content = document.createElement(clickable ? 'button' : 'div');
                    if (clickable) content.type = 'button';
                    cell.className = `fpt-${session ? session.status : available ? 'free' : 'unavailable'}`;
                    content.className = 'fpt-cell';
                    let lines;
                    if (session) {
                        lines = hour === session.start_hour
                            ? [`${session.start_time}–${session.end_time}`, session.status_label]
                            : session.status === 'locked'
                                ? ['Bloqueo administrativo']
                                : [session.instructor_name, session.student_name, session.category];
                    } else {
                        lines = [available ? 'Libre' : hour === 19 ? 'Sin inicio' : detail.period.is_active ? 'Sin inicio disponible' : 'Periodo cerrado'];
                    }
                    lines.forEach((line, index) => { const text = document.createElement(index === 0 ? 'strong' : 'small'); text.textContent = line; content.append(text); });
                    content.setAttribute('aria-label', `${dateLabel(day.date)}, ${hourLabel(hour)}: ${lines.join(', ')}`);
                    if (session) content.addEventListener('click', () => openSession(session));
                    else if (clickable) content.addEventListener('click', () => openSession(null, day.date, hour));
                    cell.append(content);
                });
            }
            wrapper.append(table); fragment.append(wrapper);
        }
        $('calendar-grid').replaceChildren(fragment);
    }

    function localDate(date) {
        return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
    }

    async function openSession(session, day, hour) {
        if (!config.canManage) {
            const fields = [['Fecha', dateLabel(session.date)], ['Horario', `${session.start_time}–${session.end_time}`], ['Estado', session.status_label], ['Estudiante', session.student_name || '—'], ['Instructor', session.instructor_name || '—'], ['Categoría', session.category_label || '—'], ['Notas', session.notes || '—']];
            $('session-details').replaceChildren(...fields.flatMap(([label, value]) => {
                const dt = document.createElement('dt'); dt.textContent = label;
                const dd = document.createElement('dd'); dd.textContent = value;
                return [dt, dd];
            }));
            $('detail-dialog').showModal();
            return;
        }
        try {
            if (!state.participants) state.participants = await request(url('participants'));
            // Do not open a stale slot if the user changed period while loading.
            if (!session && (!state.detail || !state.detail.days.some(d => d.date === day))) return;
            state.session = session;
            $('session-form').reset();
            message('session-error');
            $('reload-session').hidden = true;
            $('session-title').textContent = session ? 'Gestionar sesión FPT' : 'Nueva sesión FPT';
            $('delete-session').hidden = !session;
            fillSelect($('session-period'), state.periods.filter(p => p.is_active || p.id === session?.period).map(p => [p.id, periodLabel(p)]), session?.period ?? state.current);
            fillSelect($('session-hour'), Array.from({ length: 11 }, (_, i) => [i + 8, hourLabel(i + 8)]), session?.start_hour ?? hour);
            $('session-date').value = session?.date ?? day;
            sessionDateBounds();
            $('session-kind').value = session?.status === 'locked' ? 'locked' : 'reservation';
            $('session-payment').value = session?.status === 'paid' ? 'paid' : 'pending';
            $('session-category').value = session?.category || '';
            $('session-notes').value = session?.notes || '';
            for (const [role, choices] of [['student', state.participants.students], ['instructor', state.participants.instructors]]) {
                fillSelect($(`session-${role}`), [['', `Seleccione un ${role === 'student' ? 'estudiante' : 'instructor'}`], ...choices.map(p => [p.id, p.name])], session?.[role] || '');
                $(`${role}-mode`).value = session?.[`external_${role}_name`] ? 'external' : 'registered';
                $(`external-${role}`).value = session?.[`external_${role}_name`] || '';
                participantMode(role);
            }
            trainingMode(); updateEnd();
            if (!$('session-dialog').open) $('session-dialog').showModal();
        } catch (error) { message('page-message', error.message, true); }
    }

    function participantMode(role) {
        const external = $(`${role}-mode`).value === 'external';
        $(`session-${role}`).hidden = external; $(`session-${role}`).disabled = external;
        $(`session-${role}`).required = !external;
        $(`external-${role}`).hidden = !external; $(`external-${role}`).disabled = !external;
        $(`external-${role}`).required = external;
    }

    function trainingMode() {
        const locked = $('session-kind').value === 'locked';
        $('training-fields').hidden = locked; $('training-fields').disabled = locked;
    }

    function sessionDateBounds() {
        const period = state.periods.find(p => p.id === Number($('session-period').value));
        if (!period) return;
        $('session-date').min = period.start_date; $('session-date').max = period.end_date;
    }

    function updateEnd() { $('session-end').textContent = hourLabel(Number($('session-hour').value) + 2); }

    function openPeriod(period = null) {
        state.editingPeriod = period;
        $('period-form').reset(); message('period-error');
        $('period-start').setCustomValidity(''); $('period-end').setCustomValidity('');
        $('reload-period').hidden = true;
        $('period-title').textContent = period ? 'Gestionar periodo FPT' : 'Nuevo periodo FPT';
        const start = new Date(); start.setDate(start.getDate() + (8 - start.getDay()) % 7);
        const end = new Date(start); end.setDate(end.getDate() + 6);
        $('period-start').value = period?.start_date ?? localDate(start);
        $('period-end').value = period?.end_date ?? localDate(end);
        $('period-open').checked = period ? period.is_active : true;
        $('delete-period').hidden = !period;
        if (!$('period-dialog').open) $('period-dialog').showModal();
    }

    async function submitForm(form, errorId, action) {
        const submit = form.querySelector('[type=submit]');
        submit.disabled = true; message(errorId); message('page-message');
        try { await action(); }
        catch (error) {
            // Refresh advisory availability after a lost race, preserving inputs.
            if (error.status === 409) await refresh();
            message(errorId, error.message, true);
            if (error.code === 'stale_edit') $(errorId === 'session-error' ? 'reload-session' : 'reload-period').hidden = false;
        } finally { submit.disabled = false; }
    }

    let pendingDelete;
    function confirmDelete(kind) {
        const id = kind === 'session' ? state.session.id : state.editingPeriod.id;
        pendingDelete = { kind, id, expected_updated_at: (kind === 'session' ? state.session : state.editingPeriod).updated_at };
        message('delete-error');
        $('delete-description').textContent = kind === 'session' ? 'Se eliminará esta sesión o bloqueo y se liberará el horario. Esta acción no se puede deshacer.' : 'Se eliminará este periodo. Solo se pueden eliminar periodos sin sesiones.';
        $('delete-dialog').showModal();
    }

    document.querySelectorAll('[data-close]').forEach(button => button.addEventListener('click', () => button.closest('dialog').close()));
    $('refresh-calendar').addEventListener('click', () => { message('page-message'); refresh(); });
    $('period-select').addEventListener('change', () => { message('page-message'); refresh(Number($('period-select').value)); });
    for (const [id, direction] of [['previous-period', -1], ['next-period', 1]]) {
        $(id).addEventListener('click', () => {
            const index = state.periods.findIndex(p => p.id === state.current);
            const period = state.periods[index + direction];
            if (period) refresh(period.id);
        });
    }
    if (config.canManage) {
        $('reload-session').addEventListener('click', async () => {
            try {
                const data = await request(url('session', state.session.id));
                await openSession(data.session);
            } catch (error) { message('session-error', error.message, true); }
        });
        $('reload-period').addEventListener('click', async () => {
            try {
                const data = await request(url('period', state.editingPeriod.id));
                openPeriod(data.period);
            } catch (error) { message('period-error', error.message, true); }
        });
        $('new-period').addEventListener('click', () => openPeriod());
        $('edit-period').addEventListener('click', () => { if (state.detail) openPeriod(state.detail.period); });
        for (const role of ['student', 'instructor']) $(`${role}-mode`).addEventListener('change', () => participantMode(role));
        $('session-kind').addEventListener('change', trainingMode);
        $('session-hour').addEventListener('change', updateEnd);
        $('session-period').addEventListener('change', () => {
            sessionDateBounds();
            if ($('session-date').value < $('session-date').min || $('session-date').value > $('session-date').max) $('session-date').value = $('session-date').min;
        });
        for (const id of ['period-start', 'period-end']) $(id).addEventListener('change', () => {
            const input = $(id);
            const day = new Date(`${input.value}T12:00:00`).getDay();
            input.setCustomValidity(input.value && day !== (id === 'period-start' ? 1 : 0)
                ? (id === 'period-start' ? 'Seleccione un lunes.' : 'Seleccione un domingo.') : '');
        });
        $('session-form').addEventListener('submit', event => {
            event.preventDefault();
            submitForm(event.target, 'session-error', async () => {
                const locked = $('session-kind').value === 'locked';
                const payload = { period: Number($('session-period').value), date: $('session-date').value, start_hour: Number($('session-hour').value), status: locked ? 'locked' : $('session-payment').value, category: locked ? '' : $('session-category').value, notes: $('session-notes').value };
                if (state.session) payload.expected_updated_at = state.session.updated_at;
                for (const role of ['student', 'instructor']) {
                    const external = $(`${role}-mode`).value === 'external';
                    payload[role] = !locked && !external ? Number($(`session-${role}`).value) : null;
                    payload[`external_${role}_name`] = !locked && external ? $(`external-${role}`).value.trim() : '';
                }
                await request(state.session ? url('session', state.session.id) : url('createSession'), payload);
                $('session-dialog').close();
                if (await refresh(payload.period)) message('page-message', 'Sesión guardada.');
            });
        });
        $('period-form').addEventListener('submit', event => {
            event.preventDefault();
            submitForm(event.target, 'period-error', async () => {
                const payload = { start_date: $('period-start').value, end_date: $('period-end').value, is_active: $('period-open').checked };
                if (state.editingPeriod) payload.expected_updated_at = state.editingPeriod.updated_at;
                const data = await request(state.editingPeriod ? url('period', state.editingPeriod.id) : url('periods'), payload);
                $('period-dialog').close(); if (await refresh(data.period.id)) message('page-message', 'Periodo guardado.');
            });
        });
        $('delete-session').addEventListener('click', () => confirmDelete('session'));
        $('delete-period').addEventListener('click', () => confirmDelete('period'));
        $('confirm-delete').addEventListener('click', async () => {
            $('confirm-delete').disabled = true;
            try {
                await request(url(pendingDelete.kind === 'session' ? 'deleteSession' : 'deletePeriod', pendingDelete.id), {expected_updated_at: pendingDelete.expected_updated_at});
                $('delete-dialog').close(); $(pendingDelete.kind === 'session' ? 'session-dialog' : 'period-dialog').close();
                if (await refresh()) message('page-message', 'Eliminación completada.');
            } catch (error) {
                if (error.code === 'stale_edit') {
                    $('delete-dialog').close();
                    const kind = pendingDelete.kind;
                    message(`${kind}-error`, error.message, true);
                    $(`reload-${kind}`).hidden = false;
                } else message('delete-error', error.message, true);
            }
            finally { $('confirm-delete').disabled = false; }
        });
    }
    refresh();
})();
