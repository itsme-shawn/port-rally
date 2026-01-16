// lib/logger.ts

const formatTime = () => {
  const now = new Date();
  return now.toISOString().substring(11, 23); // HH:mm:ss.SSS
};

const styles = {
  reset: "\x1b[0m",
  cyan: "\x1b[36m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  red: "\x1b[31m",
  faint: "\x1b[2m",
  bold: "\x1b[1m",
};

export const logger = {
  info: (context: string, message: string, data?: any) => {
    printLog('INFO', context, message, data, styles.green);
  },
  debug: (context: string, message: string, data?: any) => {
    if (process.env.NODE_ENV === 'development') {
      printLog('DEBUG', context, message, data, styles.cyan);
    }
  },
  warn: (context: string, message: string, data?: any) => {
    printLog('WARN', context, message, data, styles.yellow);
  },
  error: (context: string, message: string, error?: any) => {
    printLog('ERROR', context, message, error, styles.red);
  },
  
  start: (context: string, method: string, args?: any) => {
    printLog('INFO', context, `▶▶▶ [START] ${method}`, args, styles.green);
  },
  end: (context: string, method: string, startTime: number, result?: any) => {
    const time = Date.now() - startTime;
    printLog('INFO', context, `◀◀◀ [ END ] ${method} | Time: ${time}ms`, result, styles.green);
  },
  fail: (context: string, method: string, startTime: number, error: any) => {
    const time = Date.now() - startTime;
    printLog('ERROR', context, `✘✘✘ [FAIL ] ${method} | Time: ${time}ms`, error, styles.red);
  }
};

function printLog(level: string, context: string, message: string, data: any, color: string) {
  const time = formatTime();
  const formattedLevel = level.padEnd(5);
  
  let cssColor = 'color: inherit';
  if (level === 'INFO') cssColor = 'color: #10B981';
  if (level === 'WARN') cssColor = 'color: #F59E0B';
  if (level === 'ERROR') cssColor = 'color: #EF4444';
  if (level === 'DEBUG') cssColor = 'color: #3B82F6';

  if (data) {
    console.log(`%c${time} | ${formattedLevel} | ${context} | ${message}`, cssColor, "\n", data);
  } else {
    console.log(`%c${time} | ${formattedLevel} | ${context} | ${message}`, cssColor);
  }
}
