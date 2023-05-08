from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
from config import *
import logging
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'employee'


@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('index.html')
    
@app.route("/addhome", methods=['GET', 'POST'])
def addpage():
    return render_template('insert.html')

@app.route("/findhome", methods=['GET', 'POST'])
def getpage():
    return render_template('find.html')

@app.route("/updatehome", methods=['GET', 'POST'])
def uppage():
    return render_template('update.html')

@app.route("/deletehome", methods=['GET', 'POST'])
def delpage():
    return render_template('delete.html')

@app.route("/attendencehome", methods=['GET', 'POST'])
def attendpage():
    return render_template('attendance_tracker.html')

@app.route("/payrollhome", methods=['GET', 'POST'])
def payrollpage():
    return render_template('payroll.html')

@app.route("/about", methods=['GET', 'POST'])
def about():
    return render_template('about.html')

@app.route("/positionhome", methods=['GET','POST'])
def select_position():
    return render_template('position.html')

@app.route("/szy")
def szyage():
    return render_template('zyportfolio.html')

@app.route("/lxh")
def lxhpage():
    return render_template('xhportfolio.html')

@app.route("/cyx")
def cyxpage():
    return render_template('yxportfolio.html')


@app.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['employee_id']
    employee_name = request.form['employee_name']
    contact = request.form['contact']
    email = request.form['email']
    position = request.form['position']
    payscale = request.form['payscale']
    hiredDate = request.form['hiredDate']
    emp_image_file = request.files['image']

    # Uplaod image file in S3 #
    emp_image_file_name_in_s3 = "emp_id_" + str(emp_id) + "_image_file"
    s3 = boto3.resource('s3')
    object_url = None  # Initialize object_url with a default value

    if emp_image_file.filename == "":
        return "Please select a file"
    try:
        print("Data inserted in MySQL RDS... uploading image to S3...")
        s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
        bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
        s3_location = (bucket_location['LocationConstraint'])

        if s3_location is None:
            s3_location = ''
        else:
            s3_location = '-' + s3_location

        object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
            s3_location,
            custombucket,
            emp_image_file_name_in_s3)

    except Exception as e:
        return str(e)

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    try:
        cursor.execute(insert_sql, (emp_id, employee_name, contact, email, position, payscale, hiredDate, object_url))
        db_conn.commit()
    finally:
        cursor.close()

    print("all modification done...")
    return render_template('InsertEmpInput.html', emp_id=emp_id, name=employee_name, contact=contact, email = email, position = position, payscale=payscale, hiredDate=hiredDate, image_url = object_url)

#get employee
@app.route("/getemp", methods=['GET', 'POST'])
def GetEmp():
    if request.method == 'POST':
        emp_id = request.form['query_employee_id']

        # Fetch employee data from the database
        select_sql = "SELECT * FROM employee WHERE employee_id = %s"
        cursor = db_conn.cursor()
        cursor.execute(select_sql, (emp_id))
        employee = cursor.fetchone()
        cursor.close()

        if employee:
            emp_id, employee_name, contact, email, position,payscale,hiredDate, img_src = employee
            emp_image_file_name_in_s3 = "emp_id_{0}_image_file".format(emp_id)

            # Download image URL from S3
            s3 = boto3.client('s3')
            bucket_location = s3.get_bucket_location(Bucket=custombucket)
            s3_location = bucket_location['LocationConstraint']
            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location
            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)

            return render_template('FindEmpInput.html', employee_id = emp_id, employee_name=employee_name, contact=contact, email = email, position = position, payscale=payscale, hiredDate=hiredDate, image_url = object_url)
        else:
            return "Employee not found"

    
@app.route("/deleteemp", methods=['GET', 'POST'])
def DeleteEmp():
    logging.debug(f"Request method: {request.method}")
    if request.method == 'POST':
        emp_id = request.form['delete_employee_id']
        logging.debug(f"Employee ID: {emp_id}")

        # Delete employee record from the database
        delete_sql = "DELETE FROM employee WHERE employee_id = %s"
        cursor = db_conn.cursor()
        cursor.execute(delete_sql, (emp_id))
        db_conn.commit()

        deleted_rows = cursor.rowcount
        cursor.close()

        logging.debug(f"Deleted rows: {deleted_rows}")

        # Delete employee image from S3
        if deleted_rows > 0:
            emp_image_file_name_in_s3 = "emp_id_{0}_image_file".format(emp_id)
            s3 = boto3.client('s3')

            try:
                s3.delete_object(Bucket=custombucket, Key=emp_image_file_name_in_s3)
                return render_template('DeleteEmpInput.html' )
            except Exception as e:
                return f"Employee deleted, but there was an issue deleting the image: {str(e)}"
        else:
            return "Employee not found or already deleted."

        

@app.route("/updateemp", methods=['GET', 'POST'])
def UpdateEmp():
    if request.method == 'POST':
        emp_id = request.form['update_employee_id']
        employee_name = request.form['update_employee_name']
        contact = request.form['update_contact']
        email = request.form['update_email']
        position = request.form['update_position']
        payscale = request.form['update_payscale']
        hiredDate = request.form['update_hiredDate']
        emp_image_file = request.files['update_image']

        # Update employee record in the database
        update_sql = """UPDATE employee SET employee_name = %s, contact = %s,
                        email = %s, position = %s,payscale = %s,hiredDate = %s WHERE employee_id = %s"""
        cursor = db_conn.cursor()
        cursor.execute(update_sql, (employee_name, contact, email, position, payscale, hiredDate, emp_id))
        db_conn.commit()

        updated_rows = cursor.rowcount
        cursor.close()

        if updated_rows > 0:
            # Update employee image in S3
            emp_image_file_name_in_s3 = "emp_id_{0}_image_file".format(emp_id)
            s3 = boto3.client('s3')

            try:
                if emp_image_file.filename != "":
                    # Delete existing image file
                    s3.delete_object(Bucket=custombucket, Key=emp_image_file_name_in_s3)
                    # Upload new image file
                    s3.upload_fileobj(emp_image_file, custombucket, emp_image_file_name_in_s3)
                
                # Generate object URL
                bucket_location = s3.get_bucket_location(Bucket=custombucket)
                s3_location = bucket_location['LocationConstraint']
                if s3_location is None:
                    s3_location = ''
                else:
                    s3_location = '-' + s3_location
                object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                    s3_location,
                    custombucket,
                    emp_image_file_name_in_s3)
                
                return render_template('UpdateEmpInput.html', emp_id=emp_id, name=employee_name, contact=contact, email=email, position=position, payscale=payscale, hiredDate=hiredDate, image_url=object_url)
            except Exception as e:
                return f"Employee information updated, but there was an issue updating the image: {str(e)}"
        else:
            return "Employee not found or no changes made."

        

##attendance
@app.route("/attendance", methods=['GET', 'POST'])
def record_attendance():
    employee_id = request.form['attend_employee_id']
    date = request.form['date']
    check_in_time = request.form['check_in_time']
    check_out_time = request.form['check_out_time']
    
    check_in_datetime = datetime.strptime(check_in_time, "%H:%M")
    check_out_datetime = datetime.strptime(check_out_time, "%H:%M")
    
    duration = check_out_datetime - check_in_datetime
    duration_hours = duration.total_seconds() / 3600
    
    # Insert the attendance record into the attendance table
    insert_sql = "INSERT INTO attendance VALUES (%s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    try:
        cursor.execute(insert_sql, (employee_id, date, check_in_time, check_out_time,duration_hours))
        db_conn.commit()
    finally:
        cursor.close()

    print("attendance record added...")
    return render_template('attendance_tracker_output.html', employee_id=employee_id, date=date, check_in_time = check_in_time, check_out_time  = check_out_time, duration = duration_hours)

from flask import request, render_template

@app.route("/payroll", methods=['GET', 'POST'])
def calculateSalary():
    employee_id = request.form['payroll_employee_id']
    month = int(request.form['month'])
    year = int(request.form['year'])

    # Retrieve the necessary data from the employee and attendance tables
    select_employee_sql = "SELECT employee_name, contact, email, position, payscale, hiredDate FROM employee WHERE employee_id = %s"
    select_attendance_sql = "SELECT date, check_in_time, check_out_time FROM attendance WHERE employee_id = %s AND MONTH(date) = %s AND YEAR(date) = %s"

    cursor = db_conn.cursor()

    try:
        # Retrieve employee data
        cursor.execute(select_employee_sql, (employee_id,))
        result = cursor.fetchone()
        if result is None:
            return "Employee not found"

        employee_name, contact, email, position, payscale, hiredDate = result

        # Retrieve attendance data
        cursor.execute(select_attendance_sql, (employee_id, month, year))
        results = cursor.fetchall()

        if len(results) == 0:
            return "No attendance records found for this employee in the specified month and year"

        # Calculate the total working hours
        daily_working_hours = {}
        for attendance_date, check_in_time, check_out_time in results:
            date_key = attendance_date
            work_duration = (check_out_time - check_in_time).total_seconds() / 3600
            if date_key in daily_working_hours:
                daily_working_hours[date_key] += work_duration
            else:
                daily_working_hours[date_key] = work_duration

        total_working_hours = sum(daily_working_hours.values())

        # Calculate the total salary
        total_salary = total_working_hours * payscale

        # Return the payroll data
        return render_template('payroll_output.html', emp_id=employee_id, name=employee_name, contact=contact, email=email, position=position, payscale=payscale, hiredDate=hiredDate, month=month, year=year, total_working_hours=total_working_hours, total_salary=total_salary)
    finally:
        cursor.close()

@app.route("/positionemp", methods=['GET', 'POST'])
def employees_by_position():
    if request.method == 'POST':
        position = request.form['employee_position']

        # Fetch employee data from the database
        select_sql = "SELECT * FROM employee WHERE position = %s"
        cursor = db_conn.cursor()
        cursor.execute(select_sql, (position,))
        employees = cursor.fetchall()
        cursor.close()

        # Initialize the S3 client
        s3 = boto3.client('s3')

        return render_template('positionEmpInput.html', employees=employees, position=position, s3=s3, custombucket=custombucket)
    else:
    return render_template('positionEmpInput.html')

        
        
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
