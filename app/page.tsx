'use client'

import { useState } from 'react'
import { useFraudAnalysis } from '../hooks/useFraudAnalysis'
import DossierExport from '../components/DossierExport'

export default function Dashboard() {
  const [username, setUsername] = useState('')
  const { mutate: analyzeProfile, data, isPending, isError, error } = useFraudAnalysis()

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (username) {
      // Trigger the API call
      analyzeProfile({ username, platform: 'instagram' })
    }
  }

  return (
    <div className="p-8 bg-gray-900 min-h-screen text-white">
      <h1 className="text-2xl font-bold mb-4">Threat Intelligence Dashboard</h1>
      
      <form onSubmit={handleSearch} className="mb-8">
        <input 
          type="text" 
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Enter @username"
          className="p-2 rounded bg-gray-800 border border-gray-700 text-white mr-2"
        />
        <button 
          type="submit" 
          disabled={isPending}
          className="p-2 bg-blue-600 rounded disabled:bg-gray-600"
        >
          {isPending ? 'Analyzing...' : 'Scan Profile'}
        </button>
      </form>

      {/* Loading Skeleton State */}
      {isPending && (
        <div className="animate-pulse flex flex-col gap-4">
          <div className="h-4 bg-gray-700 rounded w-1/4"></div>
          <div className="h-24 bg-gray-700 rounded w-full"></div>
          <div className="h-4 bg-gray-700 rounded w-1/2"></div>
        </div>
      )}

      {/* Error State */}
      {isError && (
        <div className="text-red-500">Error: {error.message}</div>
      )}

      {/* Success Data Render */}
      {data && (
        <div className="p-6 bg-gray-800 rounded border border-gray-700 mt-4">
          <h2 className="text-xl font-bold text-red-500">
            Fraud Risk Score: {data.fraud_risk_score}/100
          </h2>
          <p className="mt-2 text-gray-300">Target: {data.target_username}</p>
          
          <h3 className="mt-4 font-semibold text-yellow-400">Anomalies Detected:</h3>
          <ul className="list-disc pl-5 mt-2">
            {data.anomalies.map((anomaly: string, index: number) => (
              <li key={index} className="text-sm text-gray-400">{anomaly}</li>
            ))}
          </ul>

          {/* Official Evidence Dossier Export (.PDF) */}
          <DossierExport data={data} />
        </div>
      )}
    </div>
  )
}
