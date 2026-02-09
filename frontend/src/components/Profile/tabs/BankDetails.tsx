import { useState } from 'react';
import { Plus, Edit2, Trash2, X, Check } from 'lucide-react';

type BankAccount = {
  id: string;
  bankName: string;
  accountNumber: string;
  ifscCode: string;
  branch: string;
  accountHolderName: string;
  accountType: string;
  isPrimary: boolean;
};

const BankDetails = () => {
  const [isAdding, setIsAdding] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [accounts, setAccounts] = useState<BankAccount[]>([
    {
      id: '1',
      bankName: 'HDFC Bank',
      accountNumber: '12345678',
      ifscCode: 'HDFC0001234',
      branch: 'Madhapur Branch',
      accountHolderName: 'Ravi Teja',
      accountType: 'Savings',
      isPrimary: true,
    },
  ]);

  const [formData, setFormData] = useState<Omit<BankAccount, 'id' | 'isPrimary'>>({
    bankName: '',
    accountNumber: '',
    ifscCode: '',
    branch: '',
    accountHolderName: '',
    accountType: 'Savings',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleAddAccount = () => {
    if (editingId) {
      // Update existing account
      setAccounts(prev =>
        prev.map(account =>
          account.id === editingId
            ? { ...formData, id: editingId, isPrimary: account.isPrimary }
            : account
        )
      );
      setEditingId(null);
    } else {
      // Add new account
      const newAccount: BankAccount = {
        ...formData,
        id: Date.now().toString(),
        isPrimary: accounts.length === 0, // First account is primary by default
      };
      setAccounts(prev => [...prev, newAccount]);
    }
    
    // Reset form
    setFormData({
      bankName: '',
      accountNumber: '',
      ifscCode: '',
      branch: '',
      accountHolderName: '',
      accountType: 'Savings',
    });
    setIsAdding(false);
  };

  const handleEdit = (account: BankAccount) => {
    setFormData({
      bankName: account.bankName,
      accountNumber: account.accountNumber,
      ifscCode: account.ifscCode,
      branch: account.branch,
      accountHolderName: account.accountHolderName,
      accountType: account.accountType,
    });
    setEditingId(account.id);
    setIsAdding(true);
  };

  const handleDelete = (id: string) => {
    setAccounts(prev => {
      const newAccounts = prev.filter(acc => acc.id !== id);
      // If we deleted the primary account, make the first account primary
      if (newAccounts.length > 0 && !newAccounts.some(acc => acc.isPrimary)) {
        newAccounts[0].isPrimary = true;
      }
      return newAccounts;
    });
  };

  const setAsPrimary = (id: string) => {
    setAccounts(prev =>
      prev.map(account => ({
        ...account,
        isPrimary: account.id === id,
      }))
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">Bank Accounts</h2>
        {!isAdding && (
          <button
            onClick={() => {
              setIsAdding(true);
              setEditingId(null);
            }}
            className="flex items-center gap-2 bg-blue-600 text-white hover:bg-blue-700 text-sm font-medium px-4 py-2 rounded-md"
          >
            <Plus size={16} />
            Add Bank Account
          </button>
        )}
      </div>

      {isAdding && (
        <div className="border rounded-lg p-6 mb-6 bg-white">
          <h3 className="font-semibold mb-4">
            {editingId ? 'Edit Bank Account' : 'Add New Bank Account'}
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
            <div>
              <label className="block text-gray-600 mb-1">Bank Name</label>
              <input
                type="text"
                name="bankName"
                value={formData.bankName}
                onChange={handleChange}
                className="w-full p-2 border rounded"
                placeholder="e.g., HDFC Bank"
                required
              />
            </div>
            
            <div>
              <label className="block text-gray-600 mb-1">Account Number</label>
              <input
                type="text"
                name="accountNumber"
                value={formData.accountNumber}
                onChange={handleChange}
                className="w-full p-2 border rounded"
                placeholder="Enter account number"
                required
              />
            </div>
            
            <div>
              <label className="block text-gray-600 mb-1">IFSC Code</label>
              <input
                type="text"
                name="ifscCode"
                value={formData.ifscCode}
                onChange={handleChange}
                className="w-full p-2 border rounded"
                placeholder="e.g., HDFC0001234"
                required
              />
            </div>
            
            <div>
              <label className="block text-gray-600 mb-1">Branch</label>
              <input
                type="text"
                name="branch"
                value={formData.branch}
                onChange={handleChange}
                className="w-full p-2 border rounded"
                placeholder="Branch name"
                required
              />
            </div>
            
            <div>
              <label className="block text-gray-600 mb-1">Account Holder Name</label>
              <input
                type="text"
                name="accountHolderName"
                value={formData.accountHolderName}
                onChange={handleChange}
                className="w-full p-2 border rounded"
                placeholder="Account holder's name"
                required
              />
            </div>
            
            <div>
              <label className="block text-gray-600 mb-1">Account Type</label>
              <select
                name="accountType"
                value={formData.accountType}
                onChange={handleChange}
                className="w-full p-2 border rounded"
                required
              >
                <option value="Savings">Savings</option>
                <option value="Current">Current</option>
                <option value="Salary">Salary</option>
                <option value="NRE">NRE</option>
                <option value="NRO">NRO</option>
              </select>
            </div>
          </div>
          
          <div className="flex justify-end gap-3 mt-6">
            <button
              type="button"
              onClick={() => {
                setIsAdding(false);
                setEditingId(null);
                setFormData({
                  bankName: '',
                  accountNumber: '',
                  ifscCode: '',
                  branch: '',
                  accountHolderName: '',
                  accountType: 'Savings',
                });
              }}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleAddAccount}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
            >
              {editingId ? 'Update Account' : 'Add Account'}
            </button>
          </div>
        </div>
      )}

      <div className="space-y-4">
        {accounts.length === 0 ? (
          <div className="text-center py-8 border-2 border-dashed rounded-lg">
            <p className="text-gray-500">No bank accounts added yet</p>
            <button
              onClick={() => setIsAdding(true)}
              className="mt-2 text-blue-600 hover:text-blue-800 text-sm font-medium"
            >
              + Add your first bank account
            </button>
          </div>
        ) : (
          accounts.map(account => (
            <div key={account.id} className="border rounded-lg p-6 bg-white">
              <div className="flex justify-between items-start">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-lg font-medium">{account.bankName}</h3>
                    {account.isPrimary && (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        Primary
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    {account.accountHolderName} • {account.accountType}
                  </p>
                </div>
                <div className="flex gap-2">
                  {!account.isPrimary && (
                    <button
                      onClick={() => setAsPrimary(account.id)}
                      className="text-xs text-blue-600 hover:text-blue-800"
                    >
                      Set as primary
                    </button>
                  )}
                  <button
                    onClick={() => handleEdit(account)}
                    className="text-gray-500 hover:text-blue-600 p-1"
                    title="Edit"
                  >
                    <Edit2 size={16} />
                  </button>
                  {!account.isPrimary && (
                    <button
                      onClick={() => handleDelete(account.id)}
                      className="text-gray-500 hover:text-red-600 p-1"
                      title="Delete"
                    >
                      <Trash2 size={16} />
                    </button>
                  )}
                </div>
              </div>
              
              <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">Account Number</p>
                  <p>•••• •••• {account.accountNumber.slice(-4)}</p>
                </div>
                <div>
                  <p className="text-gray-500">IFSC Code</p>
                  <p>{account.ifscCode}</p>
                </div>
                <div>
                  <p className="text-gray-500">Branch</p>
                  <p>{account.branch}</p>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default BankDetails;
