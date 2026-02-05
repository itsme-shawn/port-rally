export type Currency = 'KRW' | 'USD';

/**
 * 화폐 코드를 기호로 변환
 * @param currencyCode ISO 4217 화폐 코드 (KRW, USD, EUR 등)
 * @returns 화폐 기호
 */
export function getCurrencySymbol(currencyCode: string): string {
  const currencySymbols: Record<string, string> = {
    KRW: '₩',
    USD: '$',
    EUR: '€',
    JPY: '¥',
    CNY: '¥',
    GBP: '£',
    AUD: 'A$',
    CAD: 'C$',
    CHF: 'Fr',
    HKD: 'HK$',
    SGD: 'S$',
    INR: '₹',
    RUB: '₽',
    BRL: 'R$',
    ZAR: 'R',
  };

  return currencySymbols[currencyCode.toUpperCase()] || currencyCode;
}

/**
 * 가격을 화폐 기호와 함께 포맷팅
 * @param price 가격
 * @param currencyCode 화폐 코드
 * @returns 포맷팅된 가격 문자열 (예: ₩169,100 또는 $142.50)
 */
export function formatPriceWithCurrency(price: string | number, currencyCode: string): string {
  const symbol = getCurrencySymbol(currencyCode);
  const numPrice = typeof price === 'string' ? parseFloat(price) : price;
  const formattedPrice = numPrice.toLocaleString('ko-KR');

  return `${symbol}${formattedPrice}`;
}

/**
 * 금액을 KRW로 변환
 * @param amount 금액
 * @param currency 통화
 * @param exchangeRate USD to KRW 환율
 * @returns KRW 금액
 */
export function toKRW(amount: number, currency: Currency, exchangeRate: number): number {
  if (currency === 'KRW') {
    return amount;
  }
  return amount * exchangeRate;
}

/**
 * 금액을 USD로 변환
 * @param amount 금액
 * @param currency 통화
 * @param exchangeRate USD to KRW 환율
 * @returns USD 금액
 */
export function toUSD(amount: number, currency: Currency, exchangeRate: number): number {
  if (currency === 'USD') {
    return amount;
  }
  return amount / exchangeRate;
}

/**
 * 금액을 지정된 통화로 변환
 * @param amount 금액
 * @param fromCurrency 원본 통화
 * @param toCurrency 목표 통화
 * @param exchangeRate USD to KRW 환율
 * @returns 변환된 금액
 */
export function convertCurrency(
  amount: number,
  fromCurrency: Currency,
  toCurrency: Currency,
  exchangeRate: number
): number {
  if (fromCurrency === toCurrency) {
    return amount;
  }

  if (toCurrency === 'KRW') {
    return toKRW(amount, fromCurrency, exchangeRate);
  } else {
    return toUSD(amount, fromCurrency, exchangeRate);
  }
}

/**
 * 금액 포맷팅 (천 단위 콤마)
 * @param amount 금액
 * @param decimals 소수점 자리수 (기본: 0)
 * @returns 포맷된 문자열
 */
export function formatAmount(amount: number, decimals: number = 0): string {
  return amount.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  });
}

/**
 * 통화에 따라 금액을 올바르게 포맷팅
 * - KRW: 1원 미만 절사 (소수점 없음)
 * - USD: 소수점 둘째자리까지 표시
 *
 * @param amount 금액
 * @param currency 통화
 * @returns 포맷된 문자열 (예: "₩1,000,000" or "$1,234.56")
 */
export function formatCurrency(
  amount: number,
  currency: Currency
): string {
  const symbol = getCurrencySymbol(currency);

  if (currency === 'KRW') {
    // 원화: 1원 미만 절사
    const truncated = Math.floor(amount);
    const formatted = formatAmount(truncated, 0);
    return `${symbol}${formatted}`;
  } else {
    // 달러: 소수점 둘째자리까지
    const formatted = formatAmount(amount, 2);
    return `${symbol}${formatted}`;
  }
}

/**
 * 금액을 원하는 통화로 변환하고 포맷팅
 * @param amount 금액
 * @param fromCurrency 원본 통화
 * @param toCurrency 표시할 통화
 * @param exchangeRate USD to KRW 환율
 * @returns 포맷된 문자열
 */
export function formatCurrencyConverted(
  amount: number,
  fromCurrency: Currency,
  toCurrency: Currency,
  exchangeRate: number
): string {
  const converted = convertCurrency(amount, fromCurrency, toCurrency, exchangeRate);
  return formatCurrency(converted, toCurrency);
}
