import { useState } from "react";
import ContactInformation from "./tabs/ContactInformation";
import JobInformation from "./tabs/JobInformation";
import BankDetails from "./tabs/BankDetails";
import Identification from "./tabs/Identification";

const tabs = ["Contact Information", "Job Information", "Bank Details", "Identification"];

const ProfileTabs = () => {
  const [active, setActive] = useState(0);

  const renderTab = () => {
    switch (active) {
      case 0: return <ContactInformation />;
      case 1: return <JobInformation />;
      case 2: return <BankDetails />;
      case 3: return <Identification />;
      default: return null;
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm">
      <div className="border-b flex gap-6 p-4">
        {tabs.map((tab, idx) => (
          <button
            key={idx}
            onClick={() => setActive(idx)}
            className={`pb-2 text-sm font-medium ${
              active === idx ? "border-b-2 border-blue-600 text-blue-600" : "text-gray-500"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="p-6">{renderTab()}</div>
    </div>
  );
};

export default ProfileTabs;
