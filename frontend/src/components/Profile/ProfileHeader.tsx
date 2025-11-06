const ProfileHeader = () => {
  return (
    <div className="flex items-center gap-4 bg-white p-6 rounded-xl shadow-sm">
      <img
        src="/profile.jpg"
        alt="Profile"
        className="h-20 w-20 rounded-full border"
      />
      <div>
        <h2 className="text-2xl font-semibold">Ravi Teja</h2>
        <p className="text-sm text-gray-600">Senior Product Manager</p>
        <p className="text-sm text-gray-500">Product Department</p>
      </div>
    </div>
  );
};

export default ProfileHeader;
