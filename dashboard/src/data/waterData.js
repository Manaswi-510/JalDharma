// Comprehensive Mock Data Store for Jai Dharma AI
export const SYSTEM_METRICS = {
  totalWaterAvailableML: 142.5,
  totalPredictedDemandML: 128.0,
  totalAllocatedML: 119.2,
  totalShortageML: 8.8,
  averageSatisfactionPct: 93.1,
  fairnessIndex: 0.94,
  weightedShortageKL: 12.4,
  activeNodes: 45,
  systemStatus: "Optimal • All Nodes Online",
  lastUpdated: new Date().toLocaleTimeString(),
};

export const WEEKLY_COMPARISON = [
  { day: "Mon", available: 140.0, demand: 125.4, allocated: 118.0 },
  { day: "Tue", available: 141.2, demand: 126.8, allocated: 118.5 },
  { day: "Wed", available: 143.0, demand: 129.2, allocated: 120.1 },
  { day: "Thu", available: 142.0, demand: 127.5, allocated: 119.0 },
  { day: "Fri", available: 142.5, demand: 128.0, allocated: 119.2 },
  { day: "Sat", available: 144.1, demand: 130.4, allocated: 121.0 },
  { day: "Sun", available: 143.5, demand: 128.9, allocated: 120.4 },
];

export const SHORTAGE_DISTRIBUTION = [
  { category: "Low Shortage (<10%)", count: 28, color: "#10B981", percent: 62.2 },
  { category: "Medium Shortage (10-25%)", count: 12, color: "#F59E0B", percent: 26.7 },
  { category: "High Shortage (>25%)", count: 5, color: "#EF4444", percent: 11.1 },
];

export const VILLAGES_DATABASE = [
  { id: "VIL_001", name: "Rampur", population: 6420, priority: "P1 Critical", demandKL: 320, allocatedKL: 288, shortageKL: 32, satisfaction: 90.0, status: "Medium", tank: "Tank North-A", x: 180, y: 140 },
  { id: "VIL_002", name: "Shivpur", population: 5180, priority: "P2 High", demandKL: 260, allocatedKL: 247, shortageKL: 13, satisfaction: 95.0, status: "Low", tank: "Tank Central", x: 320, y: 210 },
  { id: "VIL_003", name: "Kalyanpur", population: 8940, priority: "P1 Critical", demandKL: 450, allocatedKL: 338, shortageKL: 112, satisfaction: 75.1, status: "High", tank: "Tank East-B", x: 520, y: 160 },
  { id: "VIL_004", name: "Dholakpur", population: 4210, priority: "P3 Standard", demandKL: 210, allocatedKL: 204, shortageKL: 6, satisfaction: 97.1, status: "Low", tank: "Tank South-A", x: 260, y: 350 },
  { id: "VIL_005", name: "Kashti", population: 8138, priority: "P1 Critical", demandKL: 410, allocatedKL: 308, shortageKL: 102, satisfaction: 75.1, status: "High", tank: "Tank West-Main", x: 120, y: 280 },
  { id: "VIL_006", name: "Shrigonda", population: 7650, priority: "P2 High", demandKL: 380, allocatedKL: 361, shortageKL: 19, satisfaction: 95.0, status: "Low", tank: "Tank Central", x: 380, y: 280 },
  { id: "VIL_007", name: "Belwandi", population: 5920, priority: "P2 High", demandKL: 295, allocatedKL: 280, shortageKL: 15, satisfaction: 94.9, status: "Low", tank: "Tank East-B", x: 620, y: 230 },
  { id: "VIL_008", name: "Mandavgan", population: 6810, priority: "P1 Critical", demandKL: 340, allocatedKL: 255, shortageKL: 85, satisfaction: 75.0, status: "High", tank: "Tank South-B", x: 440, y: 390 },
  { id: "VIL_009", name: "Malegaon", population: 7574, priority: "P1 Critical", demandKL: 378, allocatedKL: 302, shortageKL: 76, satisfaction: 79.9, status: "High", tank: "Tank North-B", x: 220, y: 80 },
  { id: "VIL_010", name: "Chas", population: 4890, priority: "P2 High", demandKL: 245, allocatedKL: 235, shortageKL: 10, satisfaction: 95.9, status: "Low", tank: "Tank West-Main", x: 80, y: 370 },
  { id: "VIL_011", name: "Babhaleshwar", population: 5320, priority: "P3 Standard", demandKL: 266, allocatedKL: 255, shortageKL: 11, satisfaction: 95.9, status: "Low", tank: "Tank North-A", x: 140, y: 60 },
  { id: "VIL_012", name: "Kolgaon", population: 6150, priority: "P2 High", demandKL: 307, allocatedKL: 285, shortageKL: 22, satisfaction: 92.8, status: "Low", tank: "Tank Central", x: 400, y: 190 },
  { id: "VIL_013", name: "Pedgaon", population: 4120, priority: "P1 Critical", demandKL: 206, allocatedKL: 155, shortageKL: 51, satisfaction: 75.2, status: "High", tank: "Tank South-A", x: 310, y: 440 },
  { id: "VIL_014", name: "Adhalgaon", population: 5490, priority: "P3 Standard", demandKL: 274, allocatedKL: 260, shortageKL: 14, satisfaction: 94.9, status: "Low", tank: "Tank East-B", x: 590, y: 320 },
  { id: "VIL_015", name: "Nimgaon", population: 4780, priority: "P2 High", demandKL: 239, allocatedKL: 227, shortageKL: 12, satisfaction: 95.0, status: "Low", tank: "Tank South-B", x: 500, y: 430 },
  { id: "VIL_016", name: "Wadali", population: 3950, priority: "P3 Standard", demandKL: 198, allocatedKL: 192, shortageKL: 6, satisfaction: 97.0, status: "Low", tank: "Tank West-Main", x: 60, y: 220 },
  { id: "VIL_017", name: "Vambori", population: 6410, priority: "P2 High", demandKL: 320, allocatedKL: 288, shortageKL: 32, satisfaction: 90.0, status: "Medium", tank: "Tank North-B", x: 270, y: 40 },
  { id: "VIL_018", name: "Rahata", population: 7120, priority: "P1 Critical", demandKL: 356, allocatedKL: 320, shortageKL: 36, satisfaction: 89.9, status: "Medium", tank: "Tank North-A", x: 190, y: 190 },
  { id: "VIL_019", name: "Puntamba", population: 5880, priority: "P3 Standard", demandKL: 294, allocatedKL: 288, shortageKL: 6, satisfaction: 98.0, status: "Low", tank: "Tank Central", x: 360, y: 130 },
  { id: "VIL_020", name: "Kopargaon", population: 9200, priority: "P1 Critical", demandKL: 460, allocatedKL: 423, shortageKL: 37, satisfaction: 92.0, status: "Low", tank: "Tank North-B", x: 310, y: 70 },
  { id: "VIL_021", name: "Loni", population: 8300, priority: "P2 High", demandKL: 415, allocatedKL: 374, shortageKL: 41, satisfaction: 90.1, status: "Medium", tank: "Tank Central", x: 450, y: 110 },
  { id: "VIL_022", name: "Sangamner", population: 11500, priority: "P1 Critical", demandKL: 575, allocatedKL: 546, shortageKL: 29, satisfaction: 95.0, status: "Low", tank: "Tank West-Main", x: 50, y: 160 },
  { id: "VIL_023", name: "Akole", population: 6200, priority: "P3 Standard", demandKL: 310, allocatedKL: 304, shortageKL: 6, satisfaction: 98.1, status: "Low", tank: "Tank West-Main", x: 40, y: 90 },
  { id: "VIL_024", name: "Parner", population: 7800, priority: "P2 High", demandKL: 390, allocatedKL: 351, shortageKL: 39, satisfaction: 90.0, status: "Medium", tank: "Tank South-A", x: 200, y: 380 },
  { id: "VIL_025", name: "Nighoj", population: 5600, priority: "P2 High", demandKL: 280, allocatedKL: 252, shortageKL: 28, satisfaction: 90.0, status: "Medium", tank: "Tank South-A", x: 160, y: 440 },
  { id: "VIL_026", name: "Takli", population: 4900, priority: "P3 Standard", demandKL: 245, allocatedKL: 240, shortageKL: 5, satisfaction: 98.0, status: "Low", tank: "Tank East-B", x: 670, y: 180 },
  { id: "VIL_027", name: "Pathardi", population: 8400, priority: "P1 Critical", demandKL: 420, allocatedKL: 378, shortageKL: 42, satisfaction: 90.0, status: "Medium", tank: "Tank East-B", x: 690, y: 290 },
  { id: "VIL_028", name: "Shevgaon", population: 7900, priority: "P2 High", demandKL: 395, allocatedKL: 356, shortageKL: 39, satisfaction: 90.1, status: "Medium", tank: "Tank East-B", x: 640, y: 370 },
  { id: "VIL_029", name: "Nevasa", population: 8600, priority: "P2 High", demandKL: 430, allocatedKL: 408, shortageKL: 22, satisfaction: 94.9, status: "Low", tank: "Tank Central", x: 470, y: 240 },
  { id: "VIL_030", name: "Sonai", population: 5400, priority: "P3 Standard", demandKL: 270, allocatedKL: 265, shortageKL: 5, satisfaction: 98.1, status: "Low", tank: "Tank Central", x: 430, y: 60 },
  { id: "VIL_031", name: "Karjat", population: 8100, priority: "P1 Critical", demandKL: 405, allocatedKL: 365, shortageKL: 40, satisfaction: 90.1, status: "Medium", tank: "Tank South-B", x: 530, y: 480 },
  { id: "VIL_032", name: "Mirajgaon", population: 4600, priority: "P2 High", demandKL: 230, allocatedKL: 207, shortageKL: 23, satisfaction: 90.0, status: "Medium", tank: "Tank South-B", x: 600, y: 460 },
  { id: "VIL_033", name: "Rashin", population: 5100, priority: "P2 High", demandKL: 255, allocatedKL: 230, shortageKL: 25, satisfaction: 90.2, status: "Medium", tank: "Tank South-B", x: 470, y: 500 },
  { id: "VIL_034", name: "Kharda", population: 3800, priority: "P3 Standard", demandKL: 190, allocatedKL: 184, shortageKL: 6, satisfaction: 96.8, status: "Low", tank: "Tank South-B", x: 660, y: 490 },
  { id: "VIL_035", name: "Jamkhed", population: 9400, priority: "P1 Critical", demandKL: 470, allocatedKL: 423, shortageKL: 47, satisfaction: 90.0, status: "Medium", tank: "Tank South-B", x: 570, y: 520 },
  { id: "VIL_036", name: "Supa", population: 4300, priority: "P3 Standard", demandKL: 215, allocatedKL: 209, shortageKL: 6, satisfaction: 97.2, status: "Low", tank: "Tank South-A", x: 230, y: 310 },
  { id: "VIL_037", name: "Shirur-Border", population: 5200, priority: "P3 Standard", demandKL: 260, allocatedKL: 255, shortageKL: 5, satisfaction: 98.1, status: "Low", tank: "Tank West-Main", x: 100, y: 420 },
  { id: "VIL_038", name: "Chincholi", population: 3400, priority: "P3 Standard", demandKL: 170, allocatedKL: 167, shortageKL: 3, satisfaction: 98.2, status: "Low", tank: "Tank West-Main", x: 110, y: 190 },
  { id: "VIL_039", name: "Deulgaon", population: 4100, priority: "P3 Standard", demandKL: 205, allocatedKL: 201, shortageKL: 4, satisfaction: 98.0, status: "Low", tank: "Tank Central", x: 350, y: 340 },
  { id: "VIL_040", name: "Khangaon", population: 3600, priority: "P3 Standard", demandKL: 180, allocatedKL: 176, shortageKL: 4, satisfaction: 97.8, status: "Low", tank: "Tank North-A", x: 250, y: 180 },
  { id: "VIL_041", name: "Arangaon", population: 4700, priority: "P2 High", demandKL: 235, allocatedKL: 223, shortageKL: 12, satisfaction: 94.9, status: "Low", tank: "Tank Central", x: 420, y: 320 },
  { id: "VIL_042", name: "Bhalwani", population: 3900, priority: "P3 Standard", demandKL: 195, allocatedKL: 191, shortageKL: 4, satisfaction: 97.9, status: "Low", tank: "Tank South-A", x: 270, y: 260 },
  { id: "VIL_043", name: "Tisgaon", population: 4500, priority: "P2 High", demandKL: 225, allocatedKL: 214, shortageKL: 11, satisfaction: 95.1, status: "Low", tank: "Tank East-B", x: 570, y: 260 },
  { id: "VIL_044", name: "Karanji", population: 3700, priority: "P3 Standard", demandKL: 185, allocatedKL: 181, shortageKL: 4, satisfaction: 97.8, status: "Low", tank: "Tank East-B", x: 620, y: 140 },
  { id: "VIL_045", name: "Shrirampur", population: 10200, priority: "P1 Critical", demandKL: 510, allocatedKL: 485, shortageKL: 25, satisfaction: 95.1, status: "Low", tank: "Tank North-B", x: 230, y: 120 }
];

export const PIPELINES_DATA = [
  { id: "PIPE_001", route: "Godavari Main Trunk -> Central Junction", maxCapacityLPS: 450, currentFlowLPS: 428, utilization: 95.1, status: "Warning", pressurePSI: 94, leakDetected: false, source: "Godavari Reservoir", target: "Tank Central" },
  { id: "PIPE_002", route: "Jayakwadi Canal -> East-B Substation", maxCapacityLPS: 380, currentFlowLPS: 240, utilization: 63.2, status: "Operational", pressurePSI: 68, leakDetected: false, source: "Jayakwadi Canal", target: "Tank East-B" },
  { id: "PIPE_003", route: "Kashti Aquifer -> West-Main Storage", maxCapacityLPS: 220, currentFlowLPS: 185, utilization: 84.1, status: "Operational", pressurePSI: 78, leakDetected: false, source: "Kashti Wellfield", target: "Tank West-Main" },
  { id: "PIPE_004", route: "Central Junction -> South-A Tank", maxCapacityLPS: 300, currentFlowLPS: 275, utilization: 91.7, status: "Warning", pressurePSI: 91, leakDetected: false, source: "Tank Central", target: "Tank South-A" },
  { id: "PIPE_005", route: "North-A Feeder -> Rampur / Rahata", maxCapacityLPS: 180, currentFlowLPS: 125, utilization: 69.4, status: "Leak Detected", pressurePSI: 42, leakDetected: true, source: "Tank North-A", target: "Rampur Node" },
  { id: "PIPE_006", route: "East-B Booster -> Kalyanpur / Belwandi", maxCapacityLPS: 280, currentFlowLPS: 255, utilization: 91.1, status: "Warning", pressurePSI: 89, leakDetected: false, source: "Tank East-B", target: "Kalyanpur Node" },
  { id: "PIPE_007", route: "South-B Rural Trunk -> Karjat / Jamkhed", maxCapacityLPS: 260, currentFlowLPS: 195, utilization: 75.0, status: "Operational", pressurePSI: 72, leakDetected: false, source: "Tank South-B", target: "Jamkhed Node" },
  { id: "PIPE_008", route: "West Spur Line -> Sangamner / Akole", maxCapacityLPS: 320, currentFlowLPS: 230, utilization: 71.9, status: "Operational", pressurePSI: 69, leakDetected: false, source: "Tank West-Main", target: "Sangamner Node" }
];

export const STORAGE_TANKS = [
  { id: "TNK_01", name: "Tank Central", capacityML: 18.5, currentLevelML: 15.8, fillPct: 85.4, status: "Optimal", x: 360, y: 220 },
  { id: "TNK_02", name: "Tank North-A", capacityML: 12.0, currentLevelML: 9.8, fillPct: 81.7, status: "Optimal", x: 200, y: 150 },
  { id: "TNK_03", name: "Tank North-B", capacityML: 14.5, currentLevelML: 11.2, fillPct: 77.2, status: "Optimal", x: 280, y: 90 },
  { id: "TNK_04", name: "Tank East-B", capacityML: 16.0, currentLevelML: 10.5, fillPct: 65.6, status: "Alert", x: 560, y: 220 },
  { id: "TNK_05", name: "Tank West-Main", capacityML: 15.0, currentLevelML: 12.4, fillPct: 82.7, status: "Optimal", x: 90, y: 270 },
  { id: "TNK_06", name: "Tank South-A", capacityML: 11.5, currentLevelML: 9.6, fillPct: 83.5, status: "Optimal", x: 260, y: 380 },
  { id: "TNK_07", name: "Tank South-B", capacityML: 13.0, currentLevelML: 9.1, fillPct: 70.0, status: "Optimal", x: 510, y: 440 },
];

export const WATER_SOURCES = [
  { id: "SRC_01", name: "Godavari Major Reservoir", type: "Reservoir", capacityML: 82000, currentML: 64500, dailyFlowML: 95.0, x: 220, y: 20 },
  { id: "SRC_02", name: "Jayakwadi Canal Intake", type: "Canal", capacityML: 26000, currentML: 18200, dailyFlowML: 35.0, x: 680, y: 60 },
  { id: "SRC_03", name: "Kashti Deep Aquifer", type: "Wellfield", capacityML: 7200, currentML: 5800, dailyFlowML: 12.5, x: 30, y: 320 },
];

// Helper to generate dynamic prediction time-series based on village and range
export function generatePredictionSeries(villageId, daysCount = 14) {
  const village = VILLAGES_DATABASE.find(v => v.id === villageId) || VILLAGES_DATABASE[0];
  const baseDemand = village.demandKL;
  const series = [];
  const today = new Date();
  
  // Past days (actual demand)
  const pastDays = Math.min(Math.floor(daysCount / 2), 7);
  for (let i = pastDays; i >= 1; i--) {
    const d = new Date(today);
    d.setDate(today.getDate() - i);
    const dateStr = d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    const noise = (Math.sin(i * 1.5) * 0.08 + Math.cos(i * 0.7) * 0.05) * baseDemand;
    const actual = Math.round(baseDemand + noise);
    series.push({
      date: dateStr,
      actualDemand: actual,
      predictedDemand: null,
      confidenceHigh: null,
      confidenceLow: null,
      isForecast: false,
    });
  }

  // Today (pivot point)
  const todayStr = today.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  series.push({
    date: todayStr,
    actualDemand: baseDemand,
    predictedDemand: baseDemand,
    confidenceHigh: Math.round(baseDemand * 1.05),
    confidenceLow: Math.round(baseDemand * 0.95),
    isForecast: false,
  });

  // Future days (AI predicted demand)
  for (let i = 1; i <= daysCount; i++) {
    const d = new Date(today);
    d.setDate(today.getDate() + i);
    const dateStr = d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    // Seasonality + slight upward trend simulation
    const seasonal = Math.sin(i * 0.6) * 0.12 * baseDemand;
    const tempTrend = (i / daysCount) * 0.08 * baseDemand;
    const predicted = Math.round(baseDemand + seasonal + tempTrend);
    const spread = (0.04 + (i / daysCount) * 0.06) * predicted;
    series.push({
      date: dateStr,
      actualDemand: null,
      predictedDemand: predicted,
      confidenceHigh: Math.round(predicted + spread),
      confidenceLow: Math.round(predicted - spread),
      isForecast: true,
    });
  }

  return {
    village,
    series,
    peakDay: series.reduce((prev, curr) => (curr.predictedDemand > (prev.predictedDemand || 0) ? curr : prev), series[series.length - 1]),
    expectedVariance: "+4.2%",
    recommendedBufferKL: Math.round(baseDemand * 0.15),
  };
}

export const WATER_JUSTICE_DATA = {
  jainsFairnessIndex: 0.94,
  averageSatisfactionPct: 93.1,
  weightedShortageKL: 12.4,
  chronicDeficitVillages: [
    { name: "Kalyanpur", shortage: "24.9%", reason: "Pipeline bottleneck on East-B", recommendation: "Activate backup Godavari bypass" },
    { name: "Kashti", shortage: "24.9%", reason: "High vulnerable pop & local well drawdown", recommendation: "Increase West-Main booster pressure by +8 PSI" },
    { name: "Mandavgan", shortage: "25.0%", reason: "Agricultural peak surge", recommendation: "Enforce rotational night-time filling" },
  ],
  // Lorenz / Equity curve points: population share vs water allocation share
  equityCurve: [
    { popShare: 0, actualWaterShare: 0, perfectEquality: 0 },
    { popShare: 20, actualWaterShare: 17.5, perfectEquality: 20 },
    { popShare: 40, actualWaterShare: 36.8, perfectEquality: 40 },
    { popShare: 60, actualWaterShare: 56.4, perfectEquality: 60 },
    { popShare: 80, actualWaterShare: 77.2, perfectEquality: 80 },
    { popShare: 100, actualWaterShare: 100, perfectEquality: 100 },
  ],
  // Satisfaction spectrum (lowest to highest)
  disparityBars: [
    { name: "Mandavgan", satisfaction: 75.0, priority: "P1" },
    { name: "Kashti", satisfaction: 75.1, priority: "P1" },
    { name: "Kalyanpur", satisfaction: 75.1, priority: "P1" },
    { name: "Pedgaon", satisfaction: 75.2, priority: "P1" },
    { name: "Malegaon", satisfaction: 79.9, priority: "P1" },
    { name: "Rampur", satisfaction: 90.0, priority: "P1" },
    { name: "Vambori", satisfaction: 90.0, priority: "P2" },
    { name: "Kolgaon", satisfaction: 92.8, priority: "P2" },
    { name: "Belwandi", satisfaction: 94.9, priority: "P2" },
    { name: "Shrigonda", satisfaction: 95.0, priority: "P2" },
    { name: "Shivpur", satisfaction: 95.0, priority: "P2" },
    { name: "Chas", satisfaction: 95.9, priority: "P2" },
    { name: "Dholakpur", satisfaction: 97.1, priority: "P3" },
    { name: "Puntamba", satisfaction: 98.0, priority: "P3" },
    { name: "Sonai", satisfaction: 98.1, priority: "P3" },
  ]
};
