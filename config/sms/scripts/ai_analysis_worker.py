#!/usr/bin/env python
"""
AI Analysis Worker for PythonAnywhere Always-On Task
This script continuously scans the voluntary_report table for pending reports
and processes them with AI analysis.
"""

import os
import sys
import django
import time
import json
from datetime import timedelta
from django.utils import timezone

# Add Django project to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
django_dir = os.path.join(project_dir, '..', '..')
sys.path.insert(0, django_dir)

# Set Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Import Django models and functions
from sms.models import VoluntaryReport, ReportAnalysis
from sms.views import run_sms_voluntary_report_analysis


def run_ai_analysis_for_voluntary_hazard_report(voluntary_hazard_report):
    """
    Run AI analysis for a specific Voluntary Hazard Report (VHR) and save results to database.
    """
    try:
        print("[{}] Processing VHR {}: {}".format(
            timezone.now(), report.id, report.description[:50]
        ))
        
        # Update status to PROCESSING
        report.ai_analysis_status = 'PROCESSING'
        report.save(update_fields=['ai_analysis_status'])

        # Call OpenAI API
        response = run_sms_voluntary_hazard_report_analysis(report)
        
        # Debug: Log response type and preview
        print("[{}] API Response type: {}, length: {}, preview: '{}'".format(
            timezone.now(),
            type(response).__name__,
            len(str(response)) if response else 0,
            str(response)[:100] if response else "None"
        ))
        
        # Check for errors or empty response
        if not response:
            raise Exception("OpenAI API returned empty response")
        
        if isinstance(response, str) and response.startswith("Error:"):
            raise Exception("OpenAI API error: {}".format(response))
        
        # Validate response is not empty string
        if isinstance(response, str) and not response.strip():
            raise Exception("OpenAI API returned empty string response")
        
        # Parse JSON response with better error handling
        try:
            parsed_response = json.loads(response)
        except (json.JSONDecodeError, ValueError) as e:
            # ValueError is for older Python versions, JSONDecodeError for newer ones
            raise Exception("Invalid JSON response from OpenAI API. Response: '{}'. Error: {}".format(
                response[:200] if len(response) > 200 else response, str(e)
            ))
        
        # Handle array response - extract the first (and only) object
        if isinstance(parsed_response, list) and len(parsed_response) > 0:
            parsed_data = parsed_response[0]
        elif isinstance(parsed_response, dict):
            parsed_data = parsed_response
        else:
            raise Exception("Invalid JSON response format: expected array or object")
        
        # Create analysis record
        is_valid_value = parsed_data.get('is_valid', 'NO')
        is_valid = 'YES' if is_valid_value == 'SI' else 'NO'
        
        analysis_record = ReportAnalysis.objects.create(
            report=report,
            is_valid=is_valid,
            severity=parsed_data.get('severity', ''),
            probability=parsed_data.get('probability', ''),
            value=parsed_data.get('value', ''),
            risk_analysis=parsed_data.get('risk_analysis', []),
            recommendations=parsed_data.get('recommendations', [])
        )
        
        # Update status to COMPLETED
        report.ai_analysis_status = 'COMPLETED'
        report.save(update_fields=['ai_analysis_status'])
        
        print("[{}] Successfully completed AI analysis for report {} (Analysis ID: {})".format(
            timezone.now(), report.id, analysis_record.id
        ))
        
        return True
        
    except Exception as e:
        error_msg = "Error processing report {}: {}".format(report.id, str(e))
        print("[{}] {}".format(timezone.now(), error_msg))
        
        # Update status to FAILED
        try:
            report.ai_analysis_status = 'FAILED'
            report.save(update_fields=['ai_analysis_status'])
        except:
            pass
        
        return False


def main_worker_loop():
    """
    Main worker loop that continuously scans for pending reports.
    """
    print("[{}] AI Analysis Worker started".format(timezone.now()))
    print("[{}] Scanning for pending reports every 30 seconds...".format(timezone.now()))
    
    while True:
        try:
            # Get reports from last 48 hours with PENDING status
            yesterday = timezone.now() - timedelta(days=2)
            pending_reports = VoluntaryHazardReport.objects.filter(
                ai_analysis_status='PENDING',
                created_at__gte=yesterday
            ).order_by('created_at')

            if pending_reports.exists():
                print("[{}] Found {} pending reports".format(timezone.now(), pending_reports.count()))
                
                # Process one report at a time
                for report in pending_reports:
                    success = run_ai_analysis_for_voluntary_hazard_report(report)
                    if success:
                        print("[{}] Report {} processed successfully".format(timezone.now(), report.id))
                    else:
                        print("[{}] Report {} processing failed".format(timezone.now(), report.id))
                    
                    # Small delay between reports to prevent API rate limiting
                    time.sleep(5)
            else:
                print("[{}] No pending reports found".format(timezone.now()))
            
            # Wait 30 seconds before next scan
            time.sleep(30)
            
        except KeyboardInterrupt:
            print("[{}] Worker stopped by user".format(timezone.now()))
            break
        except Exception as e:
            print("[{}] Worker error: {}".format(timezone.now(), str(e)))
            # Wait before retrying
            time.sleep(60)


if __name__ == "__main__":
    main_worker_loop()
