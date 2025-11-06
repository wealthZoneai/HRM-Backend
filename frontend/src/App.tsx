import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import EmployeeLogin from "./pages/Employee/EmployeeLogin";
import EmployeeDashboard from "./pages/Employee/EmployeeDashboard";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Navigate to="/employeelogin" replace />} />
        <Route path="/employeelogin" element={<EmployeeLogin />} />
        <Route path="/employeedashboard" element={<EmployeeDashboard />} />
      </Routes>
    </Router>
  );
}

export default App;
