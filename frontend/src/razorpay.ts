import { type RazorpayCheckoutResult } from "./api";

const CHECKOUT_SCRIPT_URL = "https://checkout.razorpay.com/v1/checkout.js";

// The subset of Razorpay Checkout options and events used here.
export interface RazorpayOptions {
  key: string;
  amount: number;
  currency: string;
  order_id: string;
  name: string;
  description: string;
  // Seconds before Checkout gives up; kept within the seat hold.
  timeout?: number;
  handler: (result: RazorpayCheckoutResult) => void;
  modal?: { ondismiss?: () => void };
  theme?: { color?: string };
}

export interface RazorpayFailure {
  error: { description?: string; reason?: string };
}

interface RazorpayInstance {
  open: () => void;
  on: (event: "payment.failed", handler: (r: RazorpayFailure) => void) => void;
}

declare global {
  interface Window {
    Razorpay?: new (options: RazorpayOptions) => RazorpayInstance;
  }
}

let scriptPromise: Promise<void> | null = null;

// Loads Razorpay's Checkout script once, on first use.
export function loadRazorpayCheckout(): Promise<void> {
  if (window.Razorpay) {
    return Promise.resolve();
  }

  scriptPromise ??= new Promise<void>((resolve, reject) => {
    const script = document.createElement("script");
    script.src = CHECKOUT_SCRIPT_URL;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => {
      scriptPromise = null;
      script.remove();
      reject(new Error("Could not load the payment window. Try again."));
    };
    document.body.appendChild(script);
  });

  return scriptPromise;
}

export async function openRazorpayCheckout(
  options: RazorpayOptions,
  onFailure: (failure: RazorpayFailure) => void,
) {
  await loadRazorpayCheckout();

  if (!window.Razorpay) {
    throw new Error("Could not load the payment window. Try again.");
  }

  const checkout = new window.Razorpay(options);
  checkout.on("payment.failed", onFailure);
  checkout.open();
}
