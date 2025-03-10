"use client";

import { useState, useEffect } from "react";

export default function PostShowReview() {
  const [userData, setUserData] = useState<Record<string, any> | null>(null);
  const [selectedFields, setSelectedFields] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const response = await fetch(`/api/proxy?pathname=/users`, { method: "GET" });
    
        if (!response.ok) throw new Error("Failed to fetch user data");
    
        const data: Record<string, any> = await response.json();
        console.log("Fetched user data:", data);
    
        if (data.user) {
          setUserData(data.user);
    
          // default check all da boxes
          const initialSelection = Object.keys(data.user).reduce(
            (acc, key) => ({ ...acc, [key]: true }),
            {}
          );
          setSelectedFields(initialSelection);
        }
      } catch (error) {
        console.error("Failed to fetch user data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();
  }, []);

  const toggleSelection = (field: string) => {
    setSelectedFields((prev) => ({
      ...prev,
      [field]: !prev[field],
    }));
  };

  const handleSaveSelected = async () => {
    const selectedData = Object.entries(userData || {}).reduce((acc, [key, value]) => {
      if (selectedFields[key]) {
        acc[key] = value;
      }
      return acc;
    }, {} as Record<string, any>);

    if (Object.keys(selectedData).length === 0) {
      alert("Please select at least one field before saving.");
      return;
    }

    try {
      const res = await fetch("/api/proxy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pathname: "/postshow/saveSelected", body: selectedData }),
      });

      const data = await res.json();
      alert(`Selected data saved:\n${JSON.stringify(data)}`);
    } catch (error) {
      console.error("Failed to save selected data:", error);
    }
  };

  const handleSaveAll = async () => {
    try {
      const res = await fetch("/api/proxy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pathname: "/postshow/saveAll" }),
      });

      const data = await res.json();
      alert(`Full profile saved:\n${JSON.stringify(data)}`);
    } catch (error) {
      console.error("Failed to save full profile:", error);
    }
  };

  const handleDeleteAll = async () => {
    if (!confirm("Are you sure you want to delete all local data? This cannot be undone.")) return;

    try {
      const res = await fetch("/api/proxy", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pathname: "/postshow/deleteAll" }),
      });

      const data = await res.json();
      alert("Local data deleted.");

      // kill the state
      setUserData(null);
      setSelectedFields({});
    } catch (error) {
      console.error("Failed to delete user data:", error);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-black text-white p-6">
      <h1 className="text-3xl font-bold mb-2">Review Your Session Data</h1>
      <p className="mb-4 text-gray-400">Select what you want to save and send off to FAIRYLAND.</p>

      {loading ? (
        <p>Loading...</p>
      ) : !userData ? (
        <p>No user data found.</p>
      ) : (
        <div className="bg-gray-900 p-6 rounded-lg shadow-md w-full max-w-md">
          {Object.entries(userData).map(([key, value]) => (
            <div key={key} className="flex items-center justify-between border-b border-gray-700 py-2">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={selectedFields[key]}
                  onChange={() => toggleSelection(key)}
                  className="mr-2"
                />
                <span className="capitalize">{key.replace(/_/g, " ")}:</span>
              </label>
              <span className="text-gray-300">{String(value)}</span>
            </div>
          ))}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex space-x-4 mt-6">
        <button onClick={handleSaveAll} className="border-2 border-pink-500 px-4 py-2 rounded hover:bg-pink-500">
          Save Full Profile
        </button>
        <button onClick={handleSaveSelected} className="border-2 border-pink-500 px-4 py-2 rounded hover:bg-pink-500">
          Save Selected Data
        </button>
        <button onClick={handleDeleteAll} className="border-2 border-red-500 px-4 py-2 rounded hover:bg-red-500">
          Delete All Data
        </button>
      </div>
    </div>
  );
}