import streamlit as st
import sqlite3
import csv
import io

# ==========================================
# 1. OOPs: Student Class
# ==========================================
class Student:
    def __init__(self, student_id, name, course, marks):
        self.student_id = student_id
        self.name = name
        self.course = course
        self.marks = float(marks)

    def calculate_grade(self):
        """Calculates academic score/grade."""
        if self.marks >= 80:
            return "A"
        elif self.marks >= 60:
            return "B"
        elif self.marks >= 40:
            return "C"
        else:
            return "Fail"


# ==========================================
# 2. SQL: SQLite Database Functions
# ==========================================
def get_db_connection():
    return sqlite3.connect("students.db")

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id TEXT PRIMARY KEY,
            name TEXT,
            course TEXT,
            marks REAL,
            grade TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_student(student):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO students (id, name, course, marks, grade)
        VALUES (?, ?, ?, ?, ?)
    """, (student.student_id, student.name, student.course, student.marks, student.calculate_grade()))
    conn.commit()
    conn.close()

def get_all_students():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, course, marks, grade FROM students")
    records = cursor.fetchall()
    conn.close()
    return records

def get_student_by_id(student_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, course, marks, grade FROM students WHERE id = ?", (student_id,))
    record = cursor.fetchone()
    conn.close()
    return record

def delete_student_by_id(student_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0


# ==========================================
# 3. File Handling: Reports & Summary
# ==========================================
def make_csv_report(records):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Student ID", "Name", "Course", "Marks", "Grade"])
    writer.writerows(records)
    return output.getvalue()

def make_text_summary(records):
    total = len(records)
    if total == 0:
        return "No records to summarize."

    total_marks = sum(row[3] for row in records)
    avg_marks = total_marks / total

    report = "====================================\n"
    report += "     ACADEMIC PERFORMANCE SUMMARY    \n"
    report += "====================================\n"
    report += f"Total Students Enrolled: {total}\n"
    report += f"Class Average Score    : {avg_marks:.2f}%\n"
    report += "------------------------------------\n"
    report += f"{'ID':<10} {'Name':<15} {'Course':<15} {'Marks':<8} {'Grade'}\n"
    report += "------------------------------------\n"
    for r in records:
        report += f"{r[0]:<10} {r[1]:<15} {r[2]:<15} {r[3]:<8.1f} {r[4]}\n"
    report += "====================================\n"
    return report


# ==========================================
# 4. Streamlit App Interface
# ==========================================
init_db()

st.title("📚 Student Record & File Management System")

# Separate navigation items
courses_list = ["Python Programming", "Data Structures", "Electronics", "Database Systems"]
menu = st.sidebar.selectbox("Select Action", [
    "View Records", 
    "Add Student", 
    "Update Student", 
    "Delete Student", 
    "Export Reports"
])

# --- 1: VIEW RECORDS ---
if menu == "View Records":
    st.subheader("All Student Records")
    records = get_all_students()
    
    if records:
        search_query = st.text_input("🔍 Search by Student Name or ID").strip().lower()
        table_data = []
        for r in records:
            if search_query == "" or search_query in str(r[0]).lower() or search_query in str(r[1]).lower():
                table_data.append({
                    "Student ID": r[0],
                    "Name": r[1],
                    "Course": r[2],
                    "Marks": r[3],
                    "Grade": r[4]
                })
        if table_data:
            st.dataframe(table_data, use_container_width=True)
        else:
            st.warning("No matching students found.")
    else:
        st.info("No students added yet.")

# --- 2: ADD STUDENT ---
elif menu == "Add Student":
    st.subheader("➕ Add New Student")
    
    with st.form("add_student_form", clear_on_submit=True):
        sid = st.text_input("Student ID (e.g., S101)")
        name = st.text_input("Student Name")
        course = st.selectbox("Course Allocation", courses_list)
        marks = st.number_input("Academic Score (0 - 100)", min_value=0.0, max_value=100.0, step=1.0)
        
        submitted = st.form_submit_button("Add Student")
        if submitted:
            if sid.strip() == "" or name.strip() == "":
                st.error("Please fill in both Student ID and Name.")
            elif get_student_by_id(sid.strip()):
                st.error(f"Student ID '{sid}' already exists! Use the 'Update Student' menu to modify details.")
            else:
                new_student = Student(sid, name, course, marks)
                save_student(new_student)
                st.success(f"Added {name} successfully! Assigned Grade: {new_student.calculate_grade()}")

# --- 3: UPDATE STUDENT (DEDICATED SECTION) ---
elif menu == "Update Student":
    st.subheader("✏️ Update Existing Student Record")
    records = get_all_students()
    
    if not records:
        st.info("No students available to update. Add a student first.")
    else:
        # Create a dropdown list of all existing IDs and Names
        student_choices = {f"{r[0]} - {r[1]}": r[0] for r in records}
        selected_label = st.selectbox("Select Student to Update", list(student_choices.keys()))
        selected_id = student_choices[selected_label]
        
        # Load the selected student's current saved data
        current_data = get_student_by_id(selected_id)
        
        with st.form("update_form"):
            st.write(f"Editing Details for ID: **{current_data[0]}**")
            new_name = st.text_input("Student Name", value=current_data[1])
            
            # Match current course index in list
            current_course_idx = courses_list.index(current_data[2]) if current_data[2] in courses_list else 0
            new_course = st.selectbox("Course Allocation", courses_list, index=current_course_idx)
            
            new_marks = st.number_input("Academic Score (0 - 100)", min_value=0.0, max_value=100.0, value=float(current_data[3]), step=1.0)
            
            update_btn = st.form_submit_button("Update Details")
            if update_btn:
                updated_student = Student(current_data[0], new_name, new_course, new_marks)
                save_student(updated_student)
                st.success(f"Record for '{new_name}' updated successfully! New Grade: {updated_student.calculate_grade()}")

# --- 4: DELETE STUDENT ---
elif menu == "Delete Student":
    st.subheader("🗑️ Delete Student")
    sid_to_delete = st.text_input("Enter Student ID to Delete")
    
    if st.button("Delete"):
        if sid_to_delete.strip() != "":
            if delete_student_by_id(sid_to_delete):
                st.success(f"Student with ID '{sid_to_delete}' has been deleted.")
            else:
                st.error(f"No student found with ID '{sid_to_delete}'.")
        else:
            st.warning("Please enter an ID.")

# --- 5: FILE HANDLING & EXPORTS ---
elif menu == "Export Reports":
    st.subheader("📁 File Handling & Report Generation")
    records = get_all_students()
    
    if records:
        col1, col2 = st.columns(2)
        
        with col1:
            csv_data = make_csv_report(records)
            st.download_button(
                label="📥 Download Records (CSV)",
                data=csv_data,
                file_name="student_records.csv",
                mime="text/csv"
            )
            st.caption("Exports database rows into a standard CSV spreadsheet file.")

        with col2:
            txt_report = make_text_summary(records)
            st.download_button(
                label="📄 Download Summary Report (.txt)",
                data=txt_report,
                file_name="performance_summary.txt",
                mime="text/plain"
            )
            st.caption("Generates a formatted academic summary report.")
            
        st.text_area("Preview of Generated Text Summary:", txt_report, height=200)
    else:
        st.warning("No records to export. Add some students first!")