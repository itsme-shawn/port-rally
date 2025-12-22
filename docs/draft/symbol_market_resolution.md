심볼 추가 시 마켓 결정 현행 흐름과 테스트 기준

현행 로직 순서
- services/market-data/src/quote_pipeline/master_loader/master_loader.py 의 MasterLoader.load_all 이 data/kospi_master, data/kosdaq_master, data/overseas_master 에서 최신 CSV를 찾고 파싱한 뒤 securities_master 에 upsert
- services/market-data/src/quote_pipeline/services/symbol_service.py 의 SymbolService.load_kr_symbols 가 securities_master 에서 national='KR' 심볼만 캐시 (symbol -> (market, "KR"))
- SymbolService.get_market_info 는 캐시 hit 시 (market, national) 반환, miss 시 (default_market, "KR") 반환 (default_market 기본값 KRX)
- services/market-data/src/quote_pipeline/clients/kis/kis_client.py 에서 구독 심볼 추가 시 infer_market_from_symbol 로 KR/US만 판별
- services/market-data/src/quote_pipeline/clients/kis/kis_config.py 의 build_subscription 이 KR이면 국내 tr_key=symbol, 그 외는 해외 tr_key=D{exchange}{symbol} (exchange 기본 NAS)
- services/market-data/src/quote_pipeline/mappers/kis_quote_mapper.py 에서 구독 응답 DTO는 SymbolService.get_market_info 를 사용해 market/national 결정, 국내/해외 실시간 DTO는 제공 필드(dto.market, dto.exchange_code)를 그대로 사용

비고
- SymbolService.load_kr_symbols 는 현재 ingestor 생성/실행 흐름에서 호출 지점이 없음
- 해외 심볼에 대한 market/national 캐시는 로드되지 않음
- infer_market_from_symbol 는 6자리 숫자면 KR, 그 외는 US로만 분기

국내 예시
- 005930 -> KOSPI
- 196170 -> KOSDAQ

해외 EXCD별 대표 심볼 (services/market-data/data/overseas_master/overseas_all_stock_code_251213.csv 기준)
- NAS: NVDA
- NYS: AA
- AMS: AAAU
- HKS: 5 (realtime symbol은 HKS00005, Symbol 컬럼은 5)
- BAY: 현재 CSV에 없음, 확인 필요 (뉴욕 NYS 주간)
- BAQ: 현재 CSV에 없음, 확인 필요 (나스닥 NAS 주간)
- BAA: 현재 CSV에 없음, 확인 필요 (아멕스 AMS 주간)

주간 시세 전환 규칙
- BAY는 NYS 주간 시세용 EXCD
- 한국시간 기준으로 NYS 데이마켓 시간일 때만 요청 EXCD를 NYS -> BAY 로 전환해서 호출
- 데이마켓 시간이 아닌 구간은 NYS로 유지
