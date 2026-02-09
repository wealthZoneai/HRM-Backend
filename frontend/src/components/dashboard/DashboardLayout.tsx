import React, { ReactNode, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { 
  FiHome,
  FiUser,
  FiTrendingUp,
  FiBriefcase,
  FiClock,
  FiBell,
  FiCalendar,
  FiCreditCard,
  FiLogOut,
  FiMenu,
  FiX
} from "react-icons/fi";
import { BsFillMegaphoneFill } from "react-icons/bs";

type DashboardLayoutProps = {
  children: ReactNode;
};

type NavItem = {
  name: string;
  icon: React.ReactNode;
  path: string;
};

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  const navItems: NavItem[] = [
    {
      name: "Dashboard",
      icon: <FiHome size={20} />,
      path: "/employeedashboard",
    },

    { name: "Profile", icon: <FiUser size={20} />, path: "/profile" },

    {
      name: "Performance",
      icon: <FiTrendingUp size={20} />,
      path: "/performance",
    },

    {
      name: "Project Status",
      icon: <FiBriefcase size={20} />,
      path: "/project-status",
    },

    {
      name: "Announcements",
      icon: <BsFillMegaphoneFill size={20} />,
      path: "/announcements",
    },

    { name: "Attendances", icon: <FiClock size={20} />, path: "/attendances" },

    {
      name: "Notifications",
      icon: <FiBell size={20} />,
      path: "/notifications",
    },

    {
      name: "Leave Management",
      icon: <FiCalendar size={20} />,
      path: "/leave-management",
    },

    { name: "Payroll", icon: <FiCreditCard size={20} />, path: "/payroll" },
  ];

  const handleLogout = () => {
    localStorage.removeItem("authToken");
    navigate("/employeelogin");
  };

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <div
        className={`${isSidebarOpen ? "w-64" : "w-20"} 
        bg-blue-800 text-white transition-all duration-300 ease-in-out`}
      >
        <div className="p-4 flex items-center justify-between">
          {isSidebarOpen && <h1 className="text-xl font-bold">HR Portal</h1>}
          <button
            onClick={toggleSidebar}
            className="p-2 rounded-lg hover:bg-blue-700"
          >
            {isSidebarOpen ? <FiX size={24} /> : <FiMenu size={24} />}
          </button>
        </div>

        <nav className="mt-8">
          {navItems.map((item) => (
            <div
              key={item.name}
              onClick={() => navigate(item.path)}
              className={`flex items-center px-6 py-3 cursor-pointer transition-colors ${
                location.pathname === item.path
                  ? "bg-blue-700"
                  : "hover:bg-blue-700"
              }`}
            >
              <span className="mr-4">{item.icon}</span>
              {isSidebarOpen && <span className="text-sm">{item.name}</span>}
            </div>
          ))}

          <div
            className="absolute bottom-0 w-full left-0 p-4 cursor-pointer flex items-center"
            onClick={handleLogout}
          >
            <FiLogOut size={20} className="mr-4" />
            {isSidebarOpen && <span>Logout</span>}
          </div>
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-white shadow">
          <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
            <h1 className="text-xl font-semibold text-gray-900">
              {navItems.find((item) => item.path === location.pathname)?.name ||
                "Dashboard"}
            </h1>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-6 bg-gray-100">
          {children}
        </main>
      </div>
    </div>
  );
}
