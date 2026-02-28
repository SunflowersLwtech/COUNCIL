"use client";

import { useState } from "react";
import {
  MessageSquare,
  Vote,
  Eye,
  Moon,
  ArrowRight,
  Swords,
  Shield,
  SkipForward,
  Rocket,
} from "lucide-react";
const STORAGE_KEY = "council_howtoplay_seen";

interface HowToPlayProps {
  onStart: () => void;
  worldTitle?: string;
  factionNames?: { good: string; evil: string };
}

export default function HowToPlay({ onStart, worldTitle, factionNames }: HowToPlayProps) {
  const [step, setStep] = useState(0);

  const good = factionNames?.good || "Good Faction";
  const evil = factionNames?.evil || "Evil Faction";

  const handleStart = () => {
    localStorage.setItem(STORAGE_KEY, "true");
    onStart();
  };

  const handleSkip = () => {
    localStorage.setItem(STORAGE_KEY, "true");
    onStart();
  };

  const steps = [
    {
      icon: <Swords size={28} style={{ color: "var(--accent)" }} />,
      title: "Social Deduction",
      description:
        "COUNCIL is a social deduction game. Players are secretly assigned to factions — some are loyal, others are traitors hiding among you. Use conversation, logic, and intuition to uncover the truth.",
    },
    {
      icon: <Shield size={28} style={{ color: "#3b82f6" }} />,
      title: "Your Goal",
      description: `As a member of the ${good}, find and eliminate the traitors through voting. As a member of the ${evil}, blend in, deceive, and survive until you outnumber the good.`,
    },
    {
      icon: <MessageSquare size={24} style={{ color: "#22c55e" }} />,
      phase: "Discussion",
      title: "Discussion Phase",
      description:
        "Speak freely with the council. Ask questions, make accusations, share observations, or defend yourself. Watch for contradictions and suspicious behavior.",
    },
    {
      icon: <Vote size={24} style={{ color: "#f97316" }} />,
      phase: "Vote",
      title: "Voting Phase",
      description:
        "The council votes to eliminate a suspect. The player with the most votes is removed and their true role is revealed. Choose wisely — eliminating an ally weakens your faction.",
    },
    {
      icon: <Eye size={24} style={{ color: "#eab308" }} />,
      phase: "Reveal",
      title: "Reveal Phase",
      description:
        "The eliminated player's hidden role and faction are revealed to all. Use this information to refine your suspicions for the next round.",
    },
    {
      icon: <Moon size={24} style={{ color: "#8b5cf6" }} />,
      phase: "Night",
      title: "Night Phase",
      description:
        "Darkness falls. Traitors choose a target to eliminate. Special roles (Seer, Doctor) perform their secret actions. When dawn breaks, the results are revealed.",
    },
  ];

  const isLastStep = step === steps.length - 1;
  const currentStep = steps[step];

  return (
    <div className="howtoplay-container">
      <div className="howtoplay-content">
        {/* Header */}
        <div className="howtoplay-header">
          <h1 className="howtoplay-title welcome-gradient-text">
            {worldTitle ? `How to Play: ${worldTitle}` : "How to Play"}
          </h1>
          <button
            className="howtoplay-skip-btn"
            onClick={handleSkip}
            title="Skip tutorial"
          >
            <SkipForward size={14} />
            Skip
          </button>
        </div>

        {/* Progress dots */}
        <div className="howtoplay-progress">
          {steps.map((_, i) => (
            <button
              key={i}
              className={`howtoplay-dot ${i === step ? "howtoplay-dot-active" : ""} ${i < step ? "howtoplay-dot-done" : ""}`}
              onClick={() => setStep(i)}
              aria-label={`Step ${i + 1}`}
            />
          ))}
        </div>

        {/* Step content */}
        <div className="howtoplay-step glass-card animate-fade-in-up" key={step}>
          <div className="howtoplay-step-icon">{currentStep.icon}</div>
          {currentStep.phase && (
            <span className="howtoplay-phase-badge">{currentStep.phase}</span>
          )}
          <h2 className="howtoplay-step-title">{currentStep.title}</h2>
          <p className="howtoplay-step-desc">{currentStep.description}</p>
        </div>

        {/* Flow diagram (visible on overview steps) */}
        {step <= 1 && (
          <div className="howtoplay-flow animate-fade-in-up">
            <div className="howtoplay-flow-item">
              <MessageSquare size={14} />
              <span>Discussion</span>
            </div>
            <ArrowRight size={12} style={{ color: "var(--text-muted)" }} />
            <div className="howtoplay-flow-item">
              <Vote size={14} />
              <span>Vote</span>
            </div>
            <ArrowRight size={12} style={{ color: "var(--text-muted)" }} />
            <div className="howtoplay-flow-item">
              <Eye size={14} />
              <span>Reveal</span>
            </div>
            <ArrowRight size={12} style={{ color: "var(--text-muted)" }} />
            <div className="howtoplay-flow-item">
              <Moon size={14} />
              <span>Night</span>
            </div>
          </div>
        )}

        {/* Tips (shown on last step) */}
        {isLastStep && (
          <div className="howtoplay-tips glass-card animate-fade-in-up">
            <h3 className="howtoplay-tips-title">Quick Tips</h3>
            <ul className="howtoplay-tips-list">
              <li>Pay attention to who accuses whom and when</li>
              <li>Click on a character's avatar to whisper directly to them</li>
              <li>Your secret role is shown in the bottom-left badge</li>
              <li>Night results can reveal critical information</li>
            </ul>
          </div>
        )}

        {/* Navigation buttons */}
        <div className="howtoplay-actions">
          {step > 0 && (
            <button
              className="howtoplay-back-btn"
              onClick={() => setStep(step - 1)}
            >
              Back
            </button>
          )}
          {isLastStep ? (
            <button className="demo-btn howtoplay-start-btn" onClick={handleStart}>
              <Rocket size={16} />
              Got it, Start!
            </button>
          ) : (
            <button
              className="demo-btn howtoplay-next-btn"
              onClick={() => setStep(step + 1)}
            >
              Next
              <ArrowRight size={14} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
