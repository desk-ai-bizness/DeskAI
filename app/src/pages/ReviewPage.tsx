import { Navigate, useParams } from 'react-router-dom';

export function ReviewPage() {
  const { consultationId = '' } = useParams();

  if (!consultationId) {
    return <Navigate replace to="/consultations" />;
  }

  return <Navigate replace to={`/consultations/${consultationId}/live`} />;
}
