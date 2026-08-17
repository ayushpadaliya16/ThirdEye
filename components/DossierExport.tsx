'use client'

import React from 'react'
import jsPDF from 'jspdf'

interface DossierData {
  target_username: string
  fraud_risk_score: number
  metadata: {
    follower_count: number
    following_count: number
    follower_ratio: number
    account_age_days: number
    profile_pic_exists: boolean
  }
  anomalies: string[]
  nlp_analysis: {
    bio_spam_likelihood: string
    suspicious_keywords_found: string[]
  }
  report_timestamp: string
}

export default function DossierExport({ data }: { data: DossierData }) {
  
  // Helper to generate a random case ID
  const generateIncidentNumber = () => {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    let result = 'INC-'
    for (let i = 0; i < 6; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length))
    }
    return result + '-GUJ'
  }

  const generatePDF = () => {
    const doc = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4',
    })

    const incidentNumber = generateIncidentNumber()

    // --- HEADER & OFFICIAL LETTERHEAD ---
    doc.setFillColor(15, 23, 42) // Deep navy blue
    doc.rect(0, 0, 210, 45, 'F')
    
    // Top Left: Main Titles
    doc.setTextColor(255, 255, 255)
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(22) // Increased size for the shorter, punchier title
    doc.text('CYBER CELL', 14, 18)
    
    doc.setFontSize(9)
    doc.setFont('helvetica', 'normal')
    doc.text('THREAT INTELLIGENCE & OPEN SOURCE ANALYSIS DIVISION', 14, 26)
    
    doc.setTextColor(239, 68, 68) // Red color
    doc.setFont('helvetica', 'bold')
    doc.text('OFFICIAL EVIDENCE DOSSIER // RESTRICTED ACCESS', 14, 34)

    // Top Right: Case ID & Date (Right-Aligned at X: 196)
    doc.setTextColor(255, 255, 255) // Reset back to white
    doc.setFont('courier', 'bold')
    doc.setFontSize(10)
    doc.text(`CASE ID: ${incidentNumber}`, 196, 18, { align: 'right' })
    
    doc.setFontSize(9)
    doc.setFont('helvetica', 'normal')
    doc.text(`DATE GENERATED: ${new Date().toISOString().split('T')[0]}`, 196, 26, { align: 'right' })

    // --- CASE INFORMATION BOX ---
    doc.setTextColor(33, 37, 41)
    doc.setFontSize(14)
    doc.setFont('helvetica', 'bold')
    doc.text('TARGET PROFILE DETAILS', 14, 60)

    doc.setDrawColor(200, 200, 200)
    doc.line(14, 62, 100, 62)

    doc.setFontSize(10)
    doc.setFont('helvetica', 'normal')
    doc.text(`Target Username:`, 14, 72)
    doc.setFont('helvetica', 'bold')
    doc.text(data.target_username, 50, 72)
    
    doc.setFont('helvetica', 'normal')
    doc.text(`Followers: ${data.metadata.follower_count}  |  Following: ${data.metadata.following_count}`, 14, 79)
    doc.text(`Follower/Following Ratio: ${data.metadata.follower_ratio}`, 14, 86)
    doc.text(`Account Age: ${data.metadata.account_age_days} Days`, 14, 93)
    doc.text(`Custom Avatar: ${data.metadata.profile_pic_exists ? 'Verified' : 'Missing / Default'}`, 14, 100)

    // --- FRAUD RISK ASSESSMENT SECTION ---
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(14)
    doc.text('AI RISK ASSESSMENT', 120, 60)
    doc.line(120, 62, 196, 62)

    doc.setFontSize(28)
    // Red if high risk, Green if low risk
    if (data.fraud_risk_score > 70) {
      doc.setTextColor(220, 38, 38) 
    } else {
      doc.setTextColor(22, 163, 74) 
    }
    doc.text(`${data.fraud_risk_score}/100`, 120, 76)

    doc.setFontSize(10)
    doc.setTextColor(100, 100, 100)
    doc.setFont('helvetica', 'bolditalic')
    doc.text(
      data.fraud_risk_score > 70 
        ? 'STATUS: HIGH RISK (PROBABLE BOT/SCAM)' 
        : 'STATUS: LOW RISK (AUTHENTIC)',
      120,
      84
    )

    // --- DETECTED ANOMALIES ---
    doc.setTextColor(33, 37, 41)
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(14)
    doc.text('HEURISTIC ANOMALIES DETECTED', 14, 120)
    doc.line(14, 122, 196, 122)

    doc.setFont('helvetica', 'normal')
    doc.setFontSize(10)
    let yPos = 132
    data.anomalies.forEach((anomaly, index) => {
      // Use bullet points for a cleaner look
      doc.text(`• ${anomaly}`, 18, yPos)
      yPos += 8
    })

    // --- NLP ANALYSIS ---
    yPos += 6
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(14)
    doc.text('NLP & BIO SEMANTICS ANALYSIS', 14, yPos)
    yPos += 2
    doc.line(14, yPos, 196, yPos)
    yPos += 10

    doc.setFont('helvetica', 'normal')
    doc.setFontSize(10)
    doc.text(`Calculated Bio Spam Likelihood:`, 14, yPos)
    doc.setFont('helvetica', 'bold')
    doc.text(`${data.nlp_analysis.bio_spam_likelihood}`, 72, yPos)
    
    yPos += 8
    doc.setFont('helvetica', 'normal')
    doc.text(`Flagged Keywords:`, 14, yPos)
    doc.setFont('helvetica', 'italic')
    doc.text(`${data.nlp_analysis.suspicious_keywords_found.join(' | ')}`, 50, yPos)

    // --- CRYPTOGRAPHIC FOOTER & SIGN OFF ---
    yPos = 250
    doc.setDrawColor(150, 150, 150)
    doc.line(14, yPos, 196, yPos)
    
    doc.setFontSize(9)
    doc.setTextColor(80, 80, 80)
    doc.setFont('helvetica', 'bold')
    doc.text('SYSTEM INTEGRATOR / INVESTIGATOR:', 14, yPos + 8)
    doc.setFont('helvetica', 'normal')
    doc.text('Ayush Padaliya', 14, yPos + 14)

    doc.setFont('helvetica', 'bold')
    doc.text('CRYPTOGRAPHIC SIGNATURE (SHA-256):', 90, yPos + 8)
    doc.setFont('courier', 'normal')
    doc.text(`${data.report_timestamp}`, 90, yPos + 14)

    doc.setFontSize(8)
    doc.setFont('helvetica', 'italic')
    doc.text('This document was generated automatically by the SIH Threat Intelligence Platform.', 14, 285)

    // Trigger Download
    doc.save(`Evidence_${incidentNumber}_${data.target_username.replace('@', '')}.pdf`)
  }

  return (
    <button
      onClick={generatePDF}
      className="mt-8 px-6 py-3 bg-slate-800 hover:bg-slate-700 text-white font-bold rounded border border-slate-600 shadow-lg transition-all"
    >
      📄 Generate Official Evidence Dossier
    </button>
  )
}
