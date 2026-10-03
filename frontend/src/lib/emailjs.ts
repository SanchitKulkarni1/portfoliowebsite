import emailjs from "@emailjs/browser";

/**
 * EmailJS settings for the contact form. These IDs are public by design (they ship in the
 * browser bundle); abuse is limited by the allowed-origins list in the EmailJS dashboard.
 * Env vars override the defaults so a template can be swapped without a code change.
 */
const config = {
  serviceId: import.meta.env.VITE_EMAILJS_SERVICE_ID || "service_b6qtnrs",
  templateId: import.meta.env.VITE_EMAILJS_TEMPLATE_ID || "template_lx6e7v7",
  publicKey: import.meta.env.VITE_EMAILJS_PUBLIC_KEY || "BDKGclXuKIJJYSu3C",
};

export interface ContactMessage {
  name: string;
  email: string;
  subject: string;
  message: string;
}

/** Sends the contact form through EmailJS. Rejects if EmailJS reports a failure. */
export function sendContactMessage({ name, email, subject, message }: ContactMessage) {
  const sender = name.trim() || "Someone";
  const title = subject.trim() || "Message from your portfolio";
  return emailjs.send(
    config.serviceId,
    config.templateId,
    {
      // Several aliases so the template works whichever variable names it uses.
      name: sender,
      from_name: sender,
      email,
      from_email: email,
      reply_to: email,
      subject: title,
      title,
      message,
      time: new Date().toLocaleString(),
    },
    { publicKey: config.publicKey, limitRate: { id: "contact-form", throttle: 10_000 } },
  );
}
