import jsPDF from 'jspdf'
import autoTable from 'jspdf-autotable'

interface SchoolInfo {
  name: string
  address: string
  phone: string
  email: string
  logo?: string
  motto?: string
}

interface StudentReportData {
  student: {
    id: number
    full_name: string
    student_id: string
    class_name: string
  }
  academic_year: string
  term: string
  subjects: Array<{
    subject: string
    percentage: number
    grade: string
    points: number
    teacher_comment?: string
  }>
  overall_gpa: number
  term_average: number
  total_subjects: number
  class_position?: number
  total_students_in_class?: number
  attendance_percentage?: number
  conduct_grade?: string
  teacher_remarks?: string
  head_teacher_remarks?: string
}

export class ReportCardPDFGenerator {
  private doc: jsPDF
  private schoolInfo: SchoolInfo
  private currentY: number = 20

  constructor(schoolInfo: SchoolInfo) {
    this.doc = new jsPDF()
    this.schoolInfo = schoolInfo
  }

  generateReportCard(reportData: StudentReportData): void {
    this.addHeader()
    this.addStudentInfo(reportData)
    this.addAcademicResults(reportData)
    this.addSummarySection(reportData)
    this.addRemarksSection(reportData)
    this.addFooter()
  }

  private addHeader(): void {
    const { doc, schoolInfo } = this
    
    // School name (centered, large font)
    doc.setFontSize(18)
    doc.setFont('helvetica', 'bold')
    doc.text(schoolInfo.name, doc.internal.pageSize.width / 2, 25, { align: 'center' })
    
    // School motto if available
    if (schoolInfo.motto) {
      doc.setFontSize(10)
      doc.setFont('helvetica', 'italic')
      doc.text(`"${schoolInfo.motto}"`, doc.internal.pageSize.width / 2, 35, { align: 'center' })
      this.currentY = 45
    } else {
      this.currentY = 35
    }
    
    // School contact info
    doc.setFontSize(10)
    doc.setFont('helvetica', 'normal')
    doc.text(schoolInfo.address, doc.internal.pageSize.width / 2, this.currentY, { align: 'center' })
    doc.text(`Tel: ${schoolInfo.phone} | Email: ${schoolInfo.email}`, doc.internal.pageSize.width / 2, this.currentY + 8, { align: 'center' })
    
    // Title
    doc.setFontSize(16)
    doc.setFont('helvetica', 'bold')
    doc.text('STUDENT REPORT CARD', doc.internal.pageSize.width / 2, this.currentY + 25, { align: 'center' })
    
    this.currentY += 40
  }

  private addStudentInfo(reportData: StudentReportData): void {
    const { doc } = this
    const startY = this.currentY
    
    doc.setFontSize(12)
    doc.setFont('helvetica', 'normal')
    
    // Left column
    doc.text(`Student Name: ${reportData.student.full_name}`, 20, startY)
    doc.text(`Student ID: ${reportData.student.student_id}`, 20, startY + 10)
    doc.text(`Class: ${reportData.student.class_name}`, 20, startY + 20)
    
    // Right column
    doc.text(`Academic Year: ${reportData.academic_year}`, 120, startY)
    doc.text(`Term: ${reportData.term}`, 120, startY + 10)
    if (reportData.class_position && reportData.total_students_in_class) {
      doc.text(`Position: ${reportData.class_position} of ${reportData.total_students_in_class}`, 120, startY + 20)
    }
    
    this.currentY = startY + 35
  }

  private addAcademicResults(reportData: StudentReportData): void {
    const { doc } = this
    
    // Table headers
    const headers = [['Subject', 'Percentage', 'Grade', 'Points', 'Remarks']]
    
    // Table data
    const tableData = reportData.subjects.map(subject => [
      subject.subject,
      `${(subject.percentage || 0).toFixed(1)}%`,
      subject.grade || 'N/A',
      (subject.points || 0).toFixed(1),
      subject.teacher_comment || '-'
    ])
    
    // Add summary row
    tableData.push([
      'OVERALL AVERAGE',
      `${reportData.term_average.toFixed(1)}%`,
      this.getGradeFromPercentage(reportData.term_average),
      reportData.overall_gpa.toFixed(2),
      'GPA'
    ])
    
    // Generate table
    autoTable(doc, {
      startY: this.currentY,
      head: headers,
      body: tableData,
      theme: 'grid',
      styles: {
        fontSize: 10,
        cellPadding: 3
      },
      headStyles: {
        fillColor: [41, 128, 185],
        textColor: 255,
        fontStyle: 'bold'
      },
      alternateRowStyles: {
        fillColor: [245, 245, 245]
      }
    })
    
    this.currentY = (doc as any).lastAutoTable.finalY + 10
  }

  private addSummarySection(reportData: StudentReportData): void {
    const { doc } = this
    const startY = this.currentY
    
    doc.setFontSize(12)
    doc.setFont('helvetica', 'bold')
    doc.text('SUMMARY', 20, startY)
    
    doc.setFont('helvetica', 'normal')
    doc.text(`Total Subjects: ${reportData.total_subjects}`, 20, startY + 15)
    doc.text(`Term Average: ${reportData.term_average.toFixed(1)}%`, 20, startY + 25)
    doc.text(`Overall GPA: ${reportData.overall_gpa.toFixed(2)}`, 20, startY + 35)
    
    if (reportData.attendance_percentage) {
      doc.text(`Attendance: ${reportData.attendance_percentage.toFixed(1)}%`, 120, startY + 15)
    }
    
    if (reportData.conduct_grade) {
      doc.text(`Conduct: ${reportData.conduct_grade}`, 120, startY + 25)
    }
    
    if (reportData.class_position && reportData.total_students_in_class) {
      doc.text(`Class Position: ${reportData.class_position} out of ${reportData.total_students_in_class}`, 120, startY + 35)
    }
    
    this.currentY = startY + 50
  }

  private addRemarksSection(reportData: StudentReportData): void {
    const { doc } = this
    const startY = this.currentY
    
    doc.setFontSize(12)
    doc.setFont('helvetica', 'bold')
    doc.text('REMARKS', 20, startY)
    
    doc.setFont('helvetica', 'normal')
    
    if (reportData.teacher_remarks) {
      doc.text('Class Teacher:', 20, startY + 15)
      const teacherLines = doc.splitTextToSize(reportData.teacher_remarks, 170)
      doc.text(teacherLines, 20, startY + 25)
      this.currentY = startY + 25 + (teacherLines.length * 5) + 10
    }
    
    if (reportData.head_teacher_remarks) {
      doc.text('Head Teacher:', 20, this.currentY)
      const headLines = doc.splitTextToSize(reportData.head_teacher_remarks, 170)
      doc.text(headLines, 20, this.currentY + 10)
      this.currentY = this.currentY + 10 + (headLines.length * 5) + 10
    }
  }

  private addFooter(): void {
    const { doc } = this
    const pageHeight = doc.internal.pageSize.height
    
    doc.setFontSize(10)
    doc.setFont('helvetica', 'italic')
    doc.text(`Generated on: ${new Date().toLocaleDateString()}`, 20, pageHeight - 20)
    doc.text('This is a computer-generated document', doc.internal.pageSize.width / 2, pageHeight - 20, { align: 'center' })
  }

  private getGradeFromPercentage(percentage: number): string {
    if (percentage >= 90) return 'A+'
    if (percentage >= 80) return 'A'
    if (percentage >= 70) return 'B+'
    if (percentage >= 60) return 'B'
    if (percentage >= 50) return 'C+'
    if (percentage >= 40) return 'C'
    if (percentage >= 30) return 'D'
    return 'F'
  }

  downloadPDF(filename: string): void {
    this.doc.save(filename)
  }

  getPDFBlob(): Blob {
    return this.doc.output('blob')
  }
}

// School configuration - this could come from API
export const getSchoolInfo = (): SchoolInfo => {
  return {
    name: 'Ndirande High School',
    address: 'P.O. Box 123, Ndirande, Blantyre, Malawi',
    phone: '+265 1 234 567',
    email: 'info@ndirande-high.edu',
    motto: 'Excellence in Education'
  }
}
