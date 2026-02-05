import { redirect } from "next/navigation";

type Props = {
    params: Promise<{ identifier: string }>;
};

/**
 * 기존 URL 형식 (/assets/[identifier]) 리다이렉트
 *
 * 이전: /assets/KR:KRX:005930
 * 신규: /assets?national=KR&exchange=KRX&symbol=005930
 */
export default async function AssetDetailPageLegacy({ params }: Props) {
    const { identifier } = await params;

    if (!identifier) {
        redirect('/');
    }

    // identifier 파싱 (national:exchange:symbol)
    const parts = identifier.split(':');

    if (parts.length !== 3) {
        redirect('/');
    }

    const [national, exchange, symbol] = parts;

    // 새 URL 형식으로 리다이렉트
    redirect(`/assets?national=${encodeURIComponent(national)}&exchange=${encodeURIComponent(exchange)}&symbol=${encodeURIComponent(symbol)}`);
}
