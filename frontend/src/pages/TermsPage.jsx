/**
 * Terms of Service Page
 */

import React from 'react';
import { Link } from 'react-router-dom';

export function TermsPage() {
  return (
    <div className="min-h-screen bg-[#0d0d0d] text-white py-20 px-4">
      <div className="max-w-3xl mx-auto">
        <Link to="/" className="text-[#E63946] hover:underline mb-8 inline-block">
          ← Back to Home
        </Link>
        
        <h1 className="text-4xl font-bold mb-8">Terms of Service</h1>
        <p className="text-gray-400 mb-8">Last updated: December 2024</p>
        
        <div className="prose prose-invert max-w-none space-y-6 text-gray-300">
          <section>
            <h2 className="text-2xl font-bold text-white mb-4">1. Acceptance of Terms</h2>
            <p>
              By accessing or using AutoBalloon ("the Service"), you agree to be bound by these 
              Terms of Service. If you disagree with any part of these terms, you may not access 
              the Service.
            </p>
          </section>
          
          <section>
            <h2 className="text-2xl font-bold text-white mb-4">2. Description of Service</h2>
            <p>
              AutoBalloon provides automated dimension detection and ballooning for manufacturing 
              blueprints. The Service uses AI to identify dimensions and generate inspection 
              reports compatible with AS9102 standards.
            </p>
          </section>
          
          <section>
            <h2 className="text-2xl font-bold text-white mb-4">3. User Accounts</h2>
            <ul className="list-disc pl-6 space-y-2">
              <li>You must provide a valid email address to create an account</li>
              <li>You are responsible for maintaining the security of your account</li>
              <li>You must not share your account credentials with others</li>
              <li>We use passwordless authentication (magic links) for security</li>
            </ul>
          </section>
          
          <section>
            <h2 className="text-2xl font-bold text-white mb-4">4. Free and Paid Plans</h2>
            <h3 className="text-xl font-semibold text-white mb-2">Free Plan:</h3>
            <ul className="list-disc pl-6 space-y-2 mb-4">
              <li>3 blueprint processings per month</li>
              <li>Files deleted after 24 hours</li>
              <li>Basic export functionality</li>
            </ul>
            
            <h3 className="text-xl font-semibold text-white mb-2">Pro Plan ($99/month):</h3>
            <ul className="list-disc pl-6 space-y-2">
              <li>Unlimited blueprint processing</li>
              <li>Permanent cloud storage</li>
              <li>AS9102 Form 3 Excel exports</li>
              <li>Priority processing</li>
              <li>Email support</li>
            </ul>
          </section>
          
          <section>
            <h2 className="text-2xl font-bold text-white mb-4">5. Payment Terms</h2>
            <ul className="list-disc pl-6 space-y-2">
              <li>Pro subscriptions are billed monthly</li>
              <li>Payment is processed securely via Paystack</li>
              <li>You may cancel your subscription at any time</li>
              <li>Cancellation takes effect at the end of the current billing period</li>
              <li>Early Adopter pricing is locked in for the lifetime of continuous subscription</li>
            </ul>
          </section>
          
          <section>
            <h2 className="text-2xl font-bold text-white mb-4">6. Refund Policy</h2>
            <p>
              We offer a 7-day money-back guarantee for new Pro subscribers. If you're not 
              satisfied within the first 7 days, contact us for a full refund. After 7 days, 
              subscriptions are non-refundable but you may cancel future billing at any time.
            </p>
          </section>
          
          <section>
            <h2 className="text-2xl font-bold text-white mb-4">7. Acceptable Use</h2>
            <p>You agree NOT to:</p>
            <ul className="list-disc pl-6 space-y-2 mt-2">
              <li>Upload content that violates intellectual property rights</li>
              <li>Attempt to reverse engineer the Service</li>
              <li>Use the Service for any illegal purpose</li>
              <li>Share, resell, or redistribute the Service</li>
              <li>Attempt to bypass usage limits through technical means</li>
            </ul>
          </section>
          
          <section>
            <h2 className="text-2xl font-bold text-white mb-4">8. Intellectual Property</h2>
            <ul className="list-disc pl-6 space-y-2">
              <li>You retain ownership of blueprints you upload</li>
              <li>We retain ownership of the Service and its underlying technology</li>
              <li>Output reports are licensed for your use in quality inspection processes</li>
            </ul>
          </section>
          
          <section>
            <h2 className="text-2xl font-bold text-white mb-4">9. Disclaimer of Warranties</h2>
            <p>
              THE SERVICE IS PROVIDED "AS IS" WITHOUT WARRANTIES OF ANY KIND. While we strive 
              for high accuracy, AI-detected dimensions should always be verified by qualified 
              inspectors before use in manufacturing or quality processes.
            </p>
          </section>
          
          <section>
            <h2 className="text-2xl font-bold text-white mb-4">10. Limitation of Liability</h2>
            <p>
              AutoBalloon shall not be liable for any indirect, incidental, special, or 
              consequential damages arising from your use of the Service. Our total liability 
              shall not exceed the amount paid by you in the 12 months preceding the claim.
            </p>
          </section>
          
          <section>
            <h2 className="text-2xl font-bold text-white mb-4">11. Changes to Terms</h2>
            <p>
              We may modify these terms at any time. Continued use of the Service after changes 
              constitutes acceptance of the new terms. We will notify users of significant 
              changes via email.
            </p>
          </section>
          
          <section>
            <h2 className="text-2xl font-bold text-white mb-4">12. Contact</h2>
            <p>
              Questions about these terms? Contact us at:{' '}
              <a href="mailto:support@autoballoon.space" className="text-[#E63946] hover:underline">
                support@autoballoon.space
              </a>
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
