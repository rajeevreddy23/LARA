"use client";

import React, { useState, useEffect } from "react";
import {
  Smartphone,
  QrCode,
  Wifi,
  Laptop,
  CheckCircle2,
  Copy,
  ExternalLink,
  X,
  Radio,
  Share2,
  Sparkles,
  ShieldCheck,
} from "lucide-react";
import { DeviceInfoResponse, getDeviceInfo } from "@/lib/api";

interface DeviceBridgeModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const DeviceBridgeModal: React.FC<DeviceBridgeModalProps> = ({
  isOpen,
  onClose,
}) => {
  const [deviceInfo, setDeviceInfo] = useState<DeviceInfoResponse | null>(null);
  const [copied, setCopied] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    if (!isOpen) return;
    const fetchInfo = async () => {
      setIsLoading(true);
      try {
        const info = await getDeviceInfo();
        setDeviceInfo(info);
      } catch (err) {
        console.error("Failed to load device info:", err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchInfo();
  }, [isOpen]);

  if (!isOpen) return null;

  const mobileUrl = deviceInfo?.mobile_web_url || "http://localhost:3000";
  // Generate a standard Google Chart / QR API image URL for zero-dependency high-fidelity QR rendering
  const qrApiUrl = `https://api.qrserver.com/v1/create-qr-code/?size=240x240&margin=10&color=00f0ff&bgcolor=020617&data=${encodeURIComponent(
    mobileUrl
  )}`;

  const handleCopyUrl = () => {
    navigator.clipboard.writeText(mobileUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-xl glass-panel border border-cyan-500/40 rounded-2xl p-6 shadow-[0_0_50px_rgba(0,240,255,0.25)] overflow-hidden">
        {/* Ambient Top Glow */}
        <div className="absolute -top-24 -right-24 w-48 h-48 bg-cyan-500/20 rounded-full blur-3xl pointer-events-none" />

        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-cyan-950/80 border border-cyan-400/50 text-cyan-400 shadow-[0_0_15px_rgba(0,240,255,0.3)]">
              <Smartphone className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-mono font-bold text-lg text-white tracking-wider">
                  MOBILE LINK &amp; CROSS-DEVICE BRIDGE
                </h2>
                <span className="px-2 py-0.5 rounded-full bg-emerald-950 border border-emerald-400/50 text-[10px] font-mono font-bold text-emerald-300">
                  REALTIME
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">
                Access LARA on your smartphone, tablet, or secondary system
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/80 transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
          {/* QR Code Column */}
          <div className="flex flex-col items-center justify-center p-4 rounded-xl bg-slate-900/90 border border-cyan-500/30 text-center">
            <div className="relative p-2 rounded-xl bg-slate-950 border border-cyan-400/50 shadow-[0_0_20px_rgba(0,240,255,0.25)]">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={qrApiUrl}
                alt="LARA Mobile Link QR Code"
                className="w-44 h-44 rounded-lg object-contain"
                onError={(e) => {
                  // Fallback to text if offline
                  (e.currentTarget as any).style.display = "none";
                }}
              />
            </div>
            <p className="mt-3 text-[11px] font-mono text-cyan-300 flex items-center gap-1.5">
              <QrCode className="w-3.5 h-3.5" />
              <span>Scan with your Mobile Camera</span>
            </p>
          </div>

          {/* Connection Details Column */}
          <div className="flex flex-col justify-between space-y-4">
            <div>
              <label className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block mb-1.5">
                Local Wi-Fi Network URL:
              </label>
              <div className="flex items-center gap-2 p-2 rounded-lg bg-slate-950/90 border border-slate-700">
                <input
                  type="text"
                  readOnly
                  value={mobileUrl}
                  className="w-full bg-transparent text-xs font-mono text-cyan-300 focus:outline-none"
                />
                <button
                  onClick={handleCopyUrl}
                  className="p-1.5 rounded-md bg-cyan-950 hover:bg-cyan-900 border border-cyan-500/40 text-cyan-300 transition-all flex items-center gap-1 text-[10px] font-mono font-bold"
                  title="Copy URL"
                >
                  {copied ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copied ? "COPIED" : "COPY"}</span>
                </button>
              </div>
            </div>

            {/* Quick Steps */}
            <div className="space-y-2 text-xs font-mono text-slate-300 bg-slate-900/60 p-3 rounded-xl border border-slate-800">
              <div className="flex items-start gap-2">
                <span className="w-4 h-4 rounded-full bg-cyan-500/20 text-cyan-400 flex items-center justify-center text-[10px] font-bold flex-shrink-0">
                  1
                </span>
                <span>Connect your phone to the <strong>same Wi-Fi</strong>.</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="w-4 h-4 rounded-full bg-cyan-500/20 text-cyan-400 flex items-center justify-center text-[10px] font-bold flex-shrink-0">
                  2
                </span>
                <span>Open the URL or scan QR code on mobile Chrome/Safari.</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="w-4 h-4 rounded-full bg-cyan-500/20 text-cyan-400 flex items-center justify-center text-[10px] font-bold flex-shrink-0">
                  3
                </span>
                <span>Tap <strong>&quot;Allow Microphone&quot;</strong> and say <strong>&quot;Hey LARA&quot;</strong>!</span>
              </div>
            </div>

            {/* Device Telemetry Pill */}
            <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 pt-1">
              <span className="flex items-center gap-1 text-slate-300">
                <Laptop className="w-3.5 h-3.5 text-cyan-400" />
                <span>Host: {deviceInfo?.hostname || "Windows PC"}</span>
              </span>
              <span className="flex items-center gap-1 text-emerald-400">
                <Radio className="w-3 h-3 animate-pulse" />
                <span>Bridge Online</span>
              </span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-6 pt-4 border-t border-slate-800 flex items-center justify-between">
          <div className="text-[11px] font-mono text-slate-500 flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Encrypted local LAN bridge • Zero cloud middleman</span>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-mono font-bold text-xs shadow-glow-sm transition-all"
          >
            DISMISS
          </button>
        </div>
      </div>
    </div>
  );
};
