import api from './api';
import type { Incident } from '../types';

export interface UpdateIncidentPayload {
  status?: string;
  assigned_to?: string | null;
}

export async function updateIncident(
  incidentId: number,
  payload: UpdateIncidentPayload
): Promise<Incident> {
  const { data } = await api.patch<Incident>(`/incidents/${incidentId}`, payload);
  return data;
}

export async function downloadIncidentReport(incidentId: number): Promise<void> {
  const response = await api.get(`/incidents/${incidentId}/report/pdf`, {
    responseType: 'blob',
  });

  const blob = new Blob([response.data], { type: 'application/pdf' });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `Reporte_Incidente_${incidentId}.pdf`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}
