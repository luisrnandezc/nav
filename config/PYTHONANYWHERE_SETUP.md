# PythonAnywhere AI Analysis Worker Setup

## 🚀 **Overview**
This guide explains how to set up the AI Analysis Worker on PythonAnywhere to process voluntary reports in the background.

## 📋 **What We've Implemented**

### **1. Database Optimization**
- ✅ Added database index on `ai_analysis_status` field
- ✅ Optimized queries for fast scanning

### **2. Simplified Signal**
- ✅ Signal now just sets status to 'PENDING'
- ✅ No background processing in Django
- ✅ User can navigate away immediately

### **3. Worker Script**
- ✅ `ai_analysis_worker.py` - Continuous background processor
- ✅ Scans for pending reports every 30 seconds
- ✅ Processes one report at a time
- ✅ Handles errors gracefully

## 🐍 **PythonAnywhere Setup Steps**

### **Step 1: Upload Worker Script**
1. Go to PythonAnywhere Files tab
2. Navigate to your project directory
3. Upload `ai_analysis_worker.py` to the root of your project

### **Step 2: Configure Always-On Task**
1. Go to PythonAnywhere Tasks tab
2. Click "Add a new always-on task"
3. **Command**: `python ai_analysis_worker.py`
4. **Working directory**: Your project root directory
5. **Environment variables**: Add your OpenAI API key if needed

### **Step 3: Test the Setup**
1. Create a new voluntary report in Django admin
2. Check that status is set to 'PENDING'
3. Monitor the Always-On Task logs
4. Verify AI analysis completes and status changes to 'COMPLETED'

## 🔧 **Configuration Options**

### **Polling Frequency**
- **Current**: 30 seconds
- **Modify**: Change `time.sleep(30)` in worker script
- **Recommendation**: 30-60 seconds for production

### **Time Window**
- **Current**: Scan reports from last 48 hours
- **Modify**: Change `timedelta(days=2)` in worker script
- **Purpose**: Prevent scanning entire database

### **API Rate Limiting**
- **Current**: 2 second delay between reports
- **Modify**: Change `time.sleep(2)` in worker script
- **Purpose**: Respect OpenAI API limits

## 📊 **Monitoring & Logs**

### **Worker Logs**
- **Location**: PythonAnywhere Tasks tab
- **Format**: `[timestamp] message`
- **Key messages**:
  - `Worker started`
  - `Found X pending reports`
  - `Processing report X`
  - `Successfully completed`

### **Admin Interface**
- **Check status**: Django admin → SMS → Voluntary Reports
- **Status progression**: PENDING → PROCESSING → COMPLETED/FAILED
- **View results**: Check `report_analysis` records

## ⚠️ **Troubleshooting**

### **Worker Not Starting**
- Check Python path in worker script
- Verify Django settings module
- Check Always-On Task configuration

### **Reports Not Processing**
- Verify OpenAI API key
- Check worker logs for errors
- Ensure database connection

### **Performance Issues**
- Monitor query execution time
- Check database index is applied
- Consider reducing polling frequency

## 🎯 **Expected Workflow**

1. **User saves report** → Status set to 'PENDING'
2. **Worker scans** → Finds pending report
3. **Worker processes** → Calls OpenAI API
4. **Worker saves results** → Updates status to 'COMPLETED'
5. **User checks admin** → Sees completed analysis

## 🔒 **Security Considerations**

- **API keys**: Store securely in environment variables
- **Database access**: Worker uses Django ORM (secure)
- **Error handling**: Failed reports marked, not exposed
- **Logging**: No sensitive data in logs

## 📈 **Scaling Considerations**

- **Current**: Optimized for 5-10 reports daily
- **Future**: Can handle 100+ reports with current setup
- **Limitations**: Single worker, sequential processing
- **Improvements**: Multiple workers, parallel processing

---

**The system is now ready for PythonAnywhere deployment!** 🚀
