"use client";

import { useState, useEffect } from "react";
import { db, auth, createUserWithEmail, signInWithEmail, signInAnon } from "@/lib/firebase"; // Import Firebase instances
import { collection, doc, setDoc, deleteDoc } from "firebase/firestore";
import { User } from "firebase/auth";


export default function PostShowReview() {
  const [userData, setUserData] = useState<Record<string, any> | null>(null);
  const [selectedFields, setSelectedFields] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<User | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authError, setAuthError] = useState<string | null>(null);
  const [authMode, setAuthMode] = useState<'signin' | 'signup'>('signin');

  useEffect(() => {
    const unsubscribe = auth.onAuthStateChanged((currentUser) => {
      setUser(currentUser);
      if (currentUser) {
        console.log("User is signed in:", currentUser.uid);
      }
    });

    const fetchUserData = async () => {
      try {
        try {
          const response = await fetch(`/api/proxy?pathname=/users`, { method: "GET" });
          
          if (response.ok) {
            const data: Record<string, any> = await response.json();
            console.log("Fetched user data:", data);
            
            if (data.user) {
              setUserData(data.user);
              
              const initialSelection = Object.keys(data.user).reduce(
                (acc, key) => ({ ...acc, [key]: true }),
                {}
              );
              setSelectedFields(initialSelection);
              setLoading(false);
              return;
            }
          }
        } catch (backendError) {
          console.error("Backend server connection error:", backendError);
        }
        
        const localUserData = localStorage.getItem('userData');
        if (localUserData) {
          try {
            const parsedData = JSON.parse(localUserData);
            console.log("Using local storage data:", parsedData);
            
            if (parsedData.user) {
              setUserData(parsedData.user);
              
              const initialSelection = Object.keys(parsedData.user).reduce(
                (acc, key) => ({ ...acc, [key]: true }),
                {}
              );
              setSelectedFields(initialSelection);
            }
          } catch (parseError) {
            console.error("Failed to parse local storage data:", parseError);
          }
        } else {
          console.log("No user data found in local storage");
        }
      } catch (error) {
        console.error("Failed to fetch user data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();
    
    return () => unsubscribe();
  }, []);

  const toggleSelection = (field: string) => {
    setSelectedFields((prev) => ({
      ...prev,
      [field]: !prev[field],
    }));
  };

  const handleEmailSignup = async () => {
    if (!email || !password) {
      setAuthError("Email and password are required");
      return;
    }
    
    setAuthError(null);
    const result = await createUserWithEmail(email, password);
    
    if (result.error) {
      setAuthError(result.error);
    } else {
      setUser(result.user);
      setEmail("");
      setPassword("");
      alert("Account created successfully!");
    }
  };

  const handleEmailSignin = async () => {
    if (!email || !password) {
      setAuthError("Email and password are required");
      return;
    }
    
    setAuthError(null);
    const result = await signInWithEmail(email, password);
    
    if (result.error) {
      setAuthError(result.error);
    } else {
      setUser(result.user);
      setEmail("");
      setPassword("");
      alert("Signed in successfully!");
    }
  };

  const handleAnonymousSignin = async () => {
    try {
      setAuthError(null);
      const result = await signInAnon();
      
      if (result.error) {
        if (result.error.includes("admin-restricted-operation")) {
          setAuthError("Anonymous login is not enabled. Please use email authentication.");
        } else {
          setAuthError(result.error);
        }
      } else {
        setUser(result.user);
        alert("Signed in anonymously!");
      }
    } catch (error: any) {
      setAuthError(error.message || "Failed to sign in anonymously");
    }
  };

  const saveUserDataToFirebase = async (dataToSave: Record<string, any>, saveType: 'full' | 'selected') => {
    try {
      if (!auth.currentUser) {
        try {
          console.log("Attempting anonymous sign in...");
          const result = await signInAnon();
          if (result.error) {
            throw new Error(result.error);
          }
          if (!result.user) {
            throw new Error("Failed to create anonymous user");
          }
          setUser(result.user);
          console.log("Anonymous sign in successful:", result.user.uid);
        } catch (anonError: any) {
          console.error("Anonymous sign in failed:", anonError);
          const shouldSignIn = confirm("You need to be signed in to save data. Would you like to sign in with email?");
          if (!shouldSignIn) return;
          
          setAuthError("Please enter your email and password to save your data");
          return;
        }
      }

      if (!auth.currentUser) {
        throw new Error("Failed to authenticate user");
      }

      const userId = auth.currentUser.uid;
      console.log("Saving data for user:", userId);
      
      try {
        const usersCollection = collection(db, "users");
        const userDocRef = doc(usersCollection, userId);


        const dataWithTimestamp = {
          ...dataToSave,
          timestamp: new Date().toISOString(),
          user_id: userId, 
        };

        // Save the data to Firestore
        console.log("Saving data to Firestore:", dataWithTimestamp);
        await setDoc(userDocRef, dataWithTimestamp, { merge: true });

        alert(`Data (${saveType}) saved successfully to your profile!`);
      } catch (firestoreError: any) {
        console.error("Firestore error:", firestoreError);
        
        // Handle specific Firestore errors
        if (firestoreError.code === 'permission-denied') {
          alert(`Permission denied: Your Firebase security rules are preventing write access. Please check your Firestore rules in the Firebase console.`);
        } else if (firestoreError.message && firestoreError.message.includes('insufficient permissions')) {
          alert(`Insufficient permissions: Your Firebase security rules are preventing write access. Please check your Firestore rules in the Firebase console.`);
        } else {
          alert(`Failed to save ${saveType} profile: ${firestoreError.message}`);
        }
        
        // debugging
        console.error("Detailed error:", {
          code: firestoreError.code,
          message: firestoreError.message,
          details: firestoreError.details,
          stack: firestoreError.stack
        });
      }
    } catch (error: any) {
      console.error(`Failed to save ${saveType} profile:`, error);
      alert(`Failed to save ${saveType} profile: ${error.message}`);
    }
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

    await saveUserDataToFirebase(selectedData, 'selected');
  };

  const handleSaveAll = async () => {
    if (userData) {
      await saveUserDataToFirebase(userData, 'full');
    } else {
      alert("No user data to save.");
    }
  };

  const handleDeleteAll = async () => {
    if (!confirm("Are you sure you want to delete all local data and generated audio? This cannot be undone.")) return;

    try {
      try {
        const res = await fetch("/api/proxy", {
          method: "DELETE",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ pathname: "/postshow/deleteAll" }),
        });
        
        if (res.ok) {
          const data = await res.json();
          console.log("Backend delete response:", data);
        }
      } catch (backendError) {
        console.error("Backend server connection error during delete:", backendError);
      }
      
      localStorage.removeItem('userData');
      
      if (auth.currentUser) {
        const userId = auth.currentUser.uid;
        const userDocRef = doc(collection(db, "users"), userId);
        await deleteDoc(userDocRef);
        alert("All data and generated audio deleted (local and Firebase).");
      } else {
        alert("Local data and generated audio deleted.");
      }
      
      setUserData(null);
      setSelectedFields({});
    } catch (error) {
      console.error("Failed to delete user data:", error);
      alert("There was an error deleting some data. Please try again.");
    }
  };

  const handleSignOut = async () => {
    try {
      await auth.signOut();
      setUser(null);
      alert("Signed out successfully");
    } catch (error) {
      console.error("Error signing out:", error);
    }
  };
  
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-black text-white p-6">
      <h1 className="text-3xl font-bold mb-2">WELCOME TO FAIRYLAND</h1>
      <p className="mb-4 text-gray-400">An Immersive Universe - game, film, & theater</p>

      {/* Authentication Section */}
      <div className="bg-gray-900 p-6 rounded-lg shadow-md w-full max-w-md mb-6">
      <h2 className="text-2xl font-bold mb-2 text-center">Create an Account</h2>
      <p className="mb-4 text-gray-400 text-center">Receive updates of when FAIRYLAND launches!</p>
        {user ? (
          <div className="text-center">
            <p className="mb-2">Logged in as: {user.email || "Anonymous User"}</p>
            <p className="text-xs text-gray-400 mb-4">User ID: {user.uid}</p>
            <button 
              onClick={handleSignOut} 
              className="border-2 border-blue-500 px-4 py-2 rounded hover:bg-blue-500"
            >
              Sign Out
            </button>
          </div>
        ) : (
          <div>
            <div className="flex justify-center space-x-4 mb-4">
              <button 
                onClick={() => setAuthMode('signin')} 
                className={`px-4 py-2 rounded ${authMode === 'signin' ? 'bg-blue-500' : 'border border-blue-500'}`}
              >
                Sign In
              </button>
              <button 
                onClick={() => setAuthMode('signup')} 
                className={`px-4 py-2 rounded ${authMode === 'signup' ? 'bg-blue-500' : 'border border-blue-500'}`}
              >
                Sign Up
              </button>
            </div>
            
            <div className="mb-4">
              <input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full p-2 mb-2 bg-gray-800 rounded"
              />
              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full p-2 mb-2 bg-gray-800 rounded"
              />
              
              {authError && <p className="text-red-500 text-sm mb-2">{authError}</p>}
              
              <div className="flex flex-col space-y-2">
                <button 
                  onClick={authMode === 'signin' ? handleEmailSignin : handleEmailSignup} 
                  className="w-full border-2 border-blue-500 px-4 py-2 rounded hover:bg-blue-500"
                >
                  {authMode === 'signin' ? 'Sign In with Email' : 'Sign Up with Email'}
                </button>
                <p className="text-center text-gray-400 text-xs my-1">- or -</p>
                <button 
                  onClick={handleAnonymousSignin} 
                  className="w-full border-2 border-gray-500 px-4 py-2 rounded hover:bg-gray-500"
                >
                  Continue Anonymously
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
      <div className="text-center">
      <h2 className="text-2xl font-bold mb-2">Review Your Session Data</h2>
      <p className="mb-4 text-gray-400">Select what interaction data you want to save to your profile.<br></br> Your interaction data enriches your FAIRYLAND experience.</p>
      <p className="mb-4 text-gray-400"><u><a href="https://fairylandshow.com/privacy">Privacy Policy</a></u> & <u><a href="https://fairylandshow.com/terms">Terms of Use</a></u></p>
      </div>

      {/* Action Buttons - Moved above the data list */}
      <div className="flex flex-wrap justify-center gap-4 mb-6">
        <button 
          onClick={handleSaveAll} 
          className="border-2 border-pink-500 px-4 py-2 rounded hover:bg-pink-500 transition-colors"
        >
          Save Full Profile
        </button>
        <button 
          onClick={handleSaveSelected} 
          className="border-2 border-pink-500 px-4 py-2 rounded hover:bg-pink-500 transition-colors"
        >
          Save Selected Data
        </button>
        <button 
          onClick={handleDeleteAll} 
          className="border-2 border-red-500 px-4 py-2 rounded hover:bg-red-500 transition-colors"
        >
          Delete All Data & Audio
        </button>
      </div>

      {/* User Data Section */}
      {loading ? (
        <p>Loading...</p>
      ) : !userData ? (
        <p>No user data found.</p>
      ) : (
        <div className="bg-gray-900 p-6 rounded-lg shadow-md w-full max-w-md">
          <h2 className="text-xl font-semibold mb-4 text-center">Your Session Data</h2>
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
    </div>
  );
}
