// lib/firebase.ts
import { initializeApp, getApps } from 'firebase/app';
import { getFirestore, enableIndexedDbPersistence } from 'firebase/firestore';
import { 
  getAuth, 
  createUserWithEmailAndPassword, 
  signInWithEmailAndPassword, 
  signInAnonymously,
  connectAuthEmulator
} from 'firebase/auth';

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY || "",
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN || "",
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || "",
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET || "",
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID || "",
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID || "",
  measurementId: process.env.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID || "",
};

// Log Firebase config for debugging (remove in production)
console.log("Firebase config:", {
  apiKey: firebaseConfig.apiKey ? "Set" : "Not set",
  authDomain: firebaseConfig.authDomain ? "Set" : "Not set",
  projectId: firebaseConfig.projectId ? "Set" : "Not set",
  storageBucket: firebaseConfig.storageBucket ? "Set" : "Not set",
  messagingSenderId: firebaseConfig.messagingSenderId ? "Set" : "Not set",
  appId: firebaseConfig.appId ? "Set" : "Not set",
  measurementId: firebaseConfig.measurementId ? "Set" : "Not set",
});

// Initialize Firebase if it hasn't been initialized yet
const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];

// Export Firestore and Auth instances
const db = getFirestore(app);
const auth = getAuth(app);

// Enable offline persistence for Firestore (helps with permissions in some cases)
if (typeof window !== 'undefined') {
  enableIndexedDbPersistence(db)
    .catch((err) => {
      if (err.code === 'failed-precondition') {
        console.warn('Firestore persistence could not be enabled');
      } else if (err.code === 'unimplemented') {
        console.warn('Browser does not support IndexedDB persistence');
      }
    });
}

// Helper function to create a user with email and password
export const createUserWithEmail = async (email: string, password: string) => {
  try {
    const userCredential = await createUserWithEmailAndPassword(auth, email, password);
    return { user: userCredential.user, error: null };
  } catch (error: any) {
    return { user: null, error: error.message };
  }
};

// Helper function to sign in with email and password
export const signInWithEmail = async (email: string, password: string) => {
  try {
    const userCredential = await signInWithEmailAndPassword(auth, email, password);
    return { user: userCredential.user, error: null };
  } catch (error: any) {
    return { user: null, error: error.message };
  }
};

// Helper function to sign in anonymously
export const signInAnon = async () => {
  try {
    const userCredential = await signInAnonymously(auth);
    return { user: userCredential.user, error: null };
  } catch (error: any) {
    return { user: null, error: error.message };
  }
};

export { db, auth };
