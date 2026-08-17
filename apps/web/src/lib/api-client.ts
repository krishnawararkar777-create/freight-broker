import type { HealthStatus } from '@algolyra/shared';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export async function fetchHealthStatus(): Promise<HealthStatus> {
  const response = await fetch(`${API_BASE_URL}/api/health`);
  if (!response.ok) {
    throw new Error(`API health check failed with status ${response.status}: ${response.statusText}`);
  }
  return response.json();
}
