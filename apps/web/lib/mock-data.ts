export const CURRENT_USER = {
  name: "Shawn",
  avatar: "https://github.com/shadcn.png", // Placeholder
  totalBalance: 15420000, // KRW
  totalInvested: 13500000,
  dailyChange: 420000,
  dailyChangeRate: 2.8, // %
};

export const PORTFOLIO_ITEMS = [
  {
    id: "1",
    name: "Apple",
    ticker: "AAPL",
    quantity: 10,
    avgPrice: 185.5, // USD
    currentPrice: 220.3, // USD
    currency: "USD",
    dailyChangeRate: 1.2,
    logo: "🍎",
  },
  {
    id: "2",
    name: "Tesla",
    ticker: "TSLA",
    quantity: 50,
    avgPrice: 210.0,
    currentPrice: 245.8,
    currency: "USD",
    dailyChangeRate: 5.4,
    logo: "🚗",
  },
  {
    id: "3",
    name: "Samsung Electronics",
    ticker: "005930",
    quantity: 200,
    avgPrice: 65000, // KRW
    currentPrice: 72000, // KRW
    currency: "KRW",
    dailyChangeRate: -0.5,
    logo: "📱",
  },
];

export const MOCK_CHART_DATA = [
  { date: "2024-01-01", value: 13500000 },
  { date: "2024-02-01", value: 14200000 },
  { date: "2024-03-01", value: 13800000 },
  { date: "2024-04-01", value: 14500000 },
  { date: "2024-05-01", value: 15100000 },
  { date: "2024-06-01", value: 15420000 },
];
