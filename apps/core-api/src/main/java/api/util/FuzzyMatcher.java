package api.util;

/**
 * Fuzzy String Matching 유틸리티
 */
public class FuzzyMatcher {

    /**
     * Levenshtein Distance를 계산하여 유사도를 반환합니다.
     * @return 0.0 ~ 1.0 사이의 값 (1.0이 완전 일치)
     */
    public static double calculateSimilarity(String s1, String s2) {
        if (s1 == null || s2 == null) {
            return 0.0;
        }

        String str1 = s1.toLowerCase().trim();
        String str2 = s2.toLowerCase().trim();

        if (str1.equals(str2)) {
            return 1.0;
        }

        // 길이 차이가 50% 이상이면 낮은 점수 (예: "삼성" vs "삼성전자")
        int len1 = str1.length();
        int len2 = str2.length();
        int minLength = Math.min(len1, len2);
        int maxLength = Math.max(len1, len2);

        if (minLength == 0) {
            return 0.0;
        }

        double lengthRatio = (double) minLength / maxLength;
        if (lengthRatio < 0.5) {
            // 길이 차이가 너무 크면 페널티 부여
            return lengthRatio * 0.5; // 최대 0.25로 제한
        }

        int distance = levenshteinDistance(str1, str2);

        if (maxLength == 0) {
            return 1.0;
        }

        return 1.0 - ((double) distance / maxLength);
    }

    /**
     * Levenshtein Distance 계산 (편집 거리)
     */
    private static int levenshteinDistance(String s1, String s2) {
        int len1 = s1.length();
        int len2 = s2.length();

        int[][] dp = new int[len1 + 1][len2 + 1];

        for (int i = 0; i <= len1; i++) {
            dp[i][0] = i;
        }

        for (int j = 0; j <= len2; j++) {
            dp[0][j] = j;
        }

        for (int i = 1; i <= len1; i++) {
            for (int j = 1; j <= len2; j++) {
                int cost = (s1.charAt(i - 1) == s2.charAt(j - 1)) ? 0 : 1;
                dp[i][j] = Math.min(
                    Math.min(dp[i - 1][j] + 1, dp[i][j - 1] + 1),
                    dp[i - 1][j - 1] + cost
                );
            }
        }

        return dp[len1][len2];
    }

    /**
     * 여러 후보 중 가장 유사한 것을 찾습니다.
     * @return 최고 유사도와 해당 인덱스를 포함하는 MatchResult
     */
    public static <T> MatchResult<T> findBestMatch(String query, java.util.List<T> candidates,
                                                     java.util.function.Function<T, String> nameExtractor) {
        if (query == null || candidates == null || candidates.isEmpty()) {
            return new MatchResult<>(null, 0.0, -1);
        }

        T bestMatch = null;
        double bestScore = 0.0;
        int bestIndex = -1;

        for (int i = 0; i < candidates.size(); i++) {
            T candidate = candidates.get(i);
            String candidateName = nameExtractor.apply(candidate);
            double score = calculateSimilarity(query, candidateName);

            if (score > bestScore) {
                bestScore = score;
                bestMatch = candidate;
                bestIndex = i;
            }
        }

        return new MatchResult<>(bestMatch, bestScore, bestIndex);
    }

    public static class MatchResult<T> {
        private final T match;
        private final double confidence;
        private final int index;

        public MatchResult(T match, double confidence, int index) {
            this.match = match;
            this.confidence = confidence;
            this.index = index;
        }

        public T getMatch() {
            return match;
        }

        public double getConfidence() {
            return confidence;
        }

        public int getIndex() {
            return index;
        }

        public boolean hasMatch() {
            return match != null;
        }
    }
}
