import pyglet
import pyglet.font
from fontTools import ttLib
import io

def find_working_font_name(font_path: str) -> str | None:
    """폰트 파일 경로를 받아서 pyglet에서 실제로 작동하는 이름을 반환"""
    
    # fonttools로 폰트 내부 이름 전부 추출
    with open(font_path, "rb") as f:
        font_data = f.read()
    
    tt = ttLib.TTFont(io.BytesIO(font_data))
    
    candidates = set()
    for record in tt["name"].names:
        if record.nameID in (1, 2, 4, 6):
            try:
                name = record.toUnicode()
                candidates.add(name)
                # 띄어쓰기 기준으로 앞부분 조합도 추가
                parts = name.split()
                for i in range(1, len(parts)):
                    candidates.add(" ".join(parts[:i]))
            except:
                pass

    print(f"후보 이름들: {candidates}")
    
    # pyglet에 폰트 등록
    pyglet.font.add_file(font_path)
    
    # 각 후보를 have_font로 확인
    for name in sorted(candidates, key=len, reverse=True):  # 긴 이름 우선
        if pyglet.font.have_font(name):
            print(f"✅ 찾았다: {name!r}")
            return name
    
    print("❌ 작동하는 이름 없음")
    return None


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else input("폰트 파일 경로: ")
    result = find_working_font_name(path)
    print(f"\n결과: {result}")