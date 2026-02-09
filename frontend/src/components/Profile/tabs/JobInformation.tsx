import { useState } from 'react';
import { Pencil, X, Check } from 'lucide-react';

const JobInformation = () => {
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    jobTitle: 'Senior product manager',
    department: 'Product',
    manager: 'David Chen',
    employmentType: 'Full time',
    startDate: '2025-10-26',
    location: 'Head Office',
    workEmail: 'david.chen@company.com',
    employeeId: 'EMP-1001'
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Here you would typically make an API call to save the data
    setIsEditing(false);
  };

  const handleCancel = () => {
    setIsEditing(false);
  };

  const formatDate = (dateString: string) => {
    const options: Intl.DateTimeFormatOptions = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('en-US', options);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">Job Information</h2>
        {!isEditing ? (
          <button
            onClick={() => setIsEditing(true)}
            className="flex items-center gap-2 text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            <Pencil size={16} />
            Edit Job Information
          </button>
        ) : (
          <div className="flex gap-2">
            <button
              onClick={handleCancel}
              className="flex items-center gap-1 text-gray-600 hover:text-gray-800 text-sm font-medium px-3 py-1 border rounded"
            >
              <X size={16} />
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              className="flex items-center gap-1 bg-blue-600 text-white hover:bg-blue-700 text-sm font-medium px-3 py-1 rounded"
            >
              <Check size={16} />
              Save Changes
            </button>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit}>
        <div className="border rounded-lg p-6 space-y-6 bg-white">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
            {/* Job Title */}
            <div>
              <label className="block text-gray-600 mb-1">Job Title</label>
              {isEditing ? (
                <input
                  type="text"
                  name="jobTitle"
                  value={formData.jobTitle}
                  onChange={handleChange}
                  className="w-full p-2 border rounded text-sm"
                />
              ) : (
                <p className="text-sm border-b border-gray-200 pb-1">{formData.jobTitle}</p>
              )}
            </div>

            {/* Department */}
            <div>
              <label className="block text-gray-600 mb-1">Department</label>
              {isEditing ? (
                <select
                  name="department"
                  value={formData.department}
                  onChange={handleChange}
                  className="w-full p-2 border rounded text-sm"
                >
                  <option value="Product">Product</option>
                  <option value="Engineering">Engineering</option>
                  <option value="Design">Design</option>
                  <option value="Marketing">Marketing</option>
                  <option value="Sales">Sales</option>
                  <option value="HR">Human Resources</option>
                  <option value="Finance">Finance</option>
                </select>
              ) : (
                <p className="text-sm border-b border-gray-200 pb-1">{formData.department}</p>
              )}
            </div>

            {/* Manager */}
            <div>
              <label className="block text-gray-600 mb-1">Manager</label>
              {isEditing ? (
                <input
                  type="text"
                  name="manager"
                  value={formData.manager}
                  onChange={handleChange}
                  className="w-full p-2 border rounded text-sm"
                />
              ) : (
                <p className="text-sm border-b border-gray-200 pb-1">{formData.manager}</p>
              )}
            </div>

            {/* Employment Type */}
            <div>
              <label className="block text-gray-600 mb-1">Employment Type</label>
              {isEditing ? (
                <select
                  name="employmentType"
                  value={formData.employmentType}
                  onChange={handleChange}
                  className="w-full p-2 border rounded text-sm"
                >
                  <option value="Full time">Full time</option>
                  <option value="Part time">Part time</option>
                  <option value="Contract">Contract</option>
                  <option value="Internship">Internship</option>
                </select>
              ) : (
                <p className="text-sm border-b border-gray-200 pb-1">{formData.employmentType}</p>
              )}
            </div>

            {/* Start Date */}
            <div>
              <label className="block text-gray-600 mb-1">Start Date</label>
              {isEditing ? (
                <input
                  type="date"
                  name="startDate"
                  value={formData.startDate}
                  onChange={handleChange}
                  className="w-full p-2 border rounded text-sm"
                />
              ) : (
                <p className="text-sm border-b border-gray-200 pb-1">{formatDate(formData.startDate)}</p>
              )}
            </div>

            {/* Location */}
            <div>
              <label className="block text-gray-600 mb-1">Location</label>
              {isEditing ? (
                <select
                  name="location"
                  value={formData.location}
                  onChange={handleChange}
                  className="w-full p-2 border rounded text-sm"
                >
                  <option value="Head Office">Head Office</option>
                  <option value="Branch Office">Branch Office</option>
                  <option value="Remote">Remote</option>
                </select>
              ) : (
                <p className="text-sm border-b border-gray-200 pb-1">{formData.location}</p>
              )}
            </div>

            {/* Work Email */}
            <div>
              <label className="block text-gray-600 mb-1">Work Email</label>
              {isEditing ? (
                <input
                  type="email"
                  name="workEmail"
                  value={formData.workEmail}
                  onChange={handleChange}
                  className="w-full p-2 border rounded text-sm"
                />
              ) : (
                <p className="text-sm border-b border-gray-200 pb-1">{formData.workEmail}</p>
              )}
            </div>

            {/* Employee ID */}
            <div>
              <label className="block text-gray-600 mb-1">Employee ID</label>
              <p className="text-sm border-b border-gray-200 pb-1">{formData.employeeId}</p>
            </div>
          </div>
        </div>
      </form>

      {/* Job Description */}
      <div>
        <p className="text-[14px] font-semibold mb-2">Job Description</p>
        <div className="border border-gray-300 rounded-md p-4 text-[14px] text-gray-700 leading-relaxed">
          Our recruitment process is designed to be transparent, fair, and
          efficient — ensuring every candidate gets the opportunity to shine.
          Whether you're a fresher or an experienced professional, we offer
          roles that help you learn, grow, and make an impact.
        </div>
      </div>
    </div>
  );
};

export default JobInformation;
