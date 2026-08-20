import { useMutation } from '@tanstack/react-query'

// Define the shape of the data we are sending
interface AnalyzeRequest {
  username: string
  platform: string
}

export const useFraudAnalysis = () => {
  return useMutation({
    mutationFn: async (data: AnalyzeRequest) => {
      const response = await fetch('http://localhost:8000/api/analyze-profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        throw new Error('Failed to fetch AI analysis')
      }

      return response.json()
    },
  })
}
