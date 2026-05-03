-- 1. 애니메이션 정보 테이블
CREATE TABLE IF NOT EXISTS animations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL UNIQUE,
    thumbnail_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. 굿즈 매물 테이블
CREATE TABLE IF NOT EXISTS goods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    animation_id UUID REFERENCES animations(id),
    title TEXT NOT NULL,
    price INTEGER DEFAULT 0,
    image_url TEXT,
    source_url TEXT NOT NULL UNIQUE, -- 중복 수집 방지 (번개장터 상품 링크 등)
    source_platform TEXT, -- 'Bunjang', 'Junggonara' 등
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. 이벤트/팝업스토어 일정 테이블
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    animation_id UUID REFERENCES animations(id),
    title TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    location TEXT,
    detail_link TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 기본 데이터 (애니메이션 목록) 미리 추가 (선택사항)
-- INSERT INTO animations (title) VALUES ('하이큐'), ('주술회전'), ('귀멸의 칼날'), ('치이카와') ON CONFLICT DO NOTHING;
