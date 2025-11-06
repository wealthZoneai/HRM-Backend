import { useState } from 'react';
import { Pencil, X, Check } from 'lucide-react';

const ContactInformation = () => {
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    workEmail: 'Ravitejawealthzonegroupai@gmail.com',
    personalEmail: 'raviteja@gmail.com',
    phone: '123456789',
    address: '451, Design',
    fullName: 'Ravi Teja',
    empId: 'ID 78564',
    dob: '10/11/2002',
    gender: 'Male'
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
    // Reset form data if needed
    setIsEditing(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">Contact Information</h2>
        {!isEditing ? (
          <button
            onClick={() => setIsEditing(true)}
            className="flex items-center gap-2 text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            <Pencil size={16} />
            Edit Profile
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
        <section className="border rounded-lg p-4 mb-6">
          <h3 className="font-semibold mb-4">Contact Details</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
            <div>
              <label className="block text-gray-500 mb-1">Work mail</label>
              {isEditing ? (
                <input
                  type="email"
                  name="workEmail"
                  value={formData.workEmail}
                  onChange={handleChange}
                  className="w-full p-2 border rounded"
                />
              ) : (
                <p>{formData.workEmail}</p>
              )}
            </div>
            <div>
              <label className="block text-gray-500 mb-1">Personal mail id</label>
              {isEditing ? (
                <input
                  type="email"
                  name="personalEmail"
                  value={formData.personalEmail}
                  onChange={handleChange}
                  className="w-full p-2 border rounded"
                />
              ) : (
                <p>{formData.personalEmail}</p>
              )}
            </div>

            <div>
              <label className="block text-gray-500 mb-1">Phone number</label>
              {isEditing ? (
                <input
                  type="tel"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  className="w-full p-2 border rounded"
                />
              ) : (
                <p>{formData.phone}</p>
              )}
            </div>
            <div>
              <label className="block text-gray-500 mb-1">Address</label>
              {isEditing ? (
                <input
                  type="text"
                  name="address"
                  value={formData.address}
                  onChange={handleChange}
                  className="w-full p-2 border rounded"
                />
              ) : (
                <p>{formData.address}</p>
              )}
            </div>
          </div>
        </section>

        <section className="border rounded-lg p-4">
          <h3 className="font-semibold mb-4">Personal Information</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
            <div>
              <label className="block text-gray-500 mb-1">Full name</label>
              {isEditing ? (
                <input
                  type="text"
                  name="fullName"
                  value={formData.fullName}
                  onChange={handleChange}
                  className="w-full p-2 border rounded"
                />
              ) : (
                <p>{formData.fullName}</p>
              )}
            </div>
            <div>
              <label className="block text-gray-500 mb-1">Emp ID</label>
              <p>{formData.empId}</p>
            </div>

            <div>
              <label className="block text-gray-500 mb-1">Date of Birth</label>
              {isEditing ? (
                <input
                  type="date"
                  name="dob"
                  value={formData.dob}
                  onChange={handleChange}
                  className="w-full p-2 border rounded"
                />
              ) : (
                <p>{formData.dob}</p>
              )}
            </div>
            <div>
              <label className="block text-gray-500 mb-1">Gender</label>
              {isEditing ? (
                <select
                  name="gender"
                  value={formData.gender}
                  onChange={handleChange}
                  className="w-full p-2 border rounded"
                >
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                  <option value="Prefer not to say">Prefer not to say</option>
                </select>
              ) : (
                <p>{formData.gender}</p>
              )}
            </div>
          </div>
        </section>
      </form>
    </div>
  );
};

export default ContactInformation;
