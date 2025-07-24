import os
import re

# --- 설정 부분 ---
# 이미지 폴더 경로
image_folder = 'image'
# 수정할 Streamlit 앱 파일 경로
app_file = 'streamlit_app.py'

# 한글 파일명을 영어로 변환할 규칙 정의
# 직접 필요한 만큼 추가하거나 수정하세요.
rename_map = {
    # Intro & Overview
    "스피커.webp": "speaker.webp",
    "기중기.jpg": "crane.jpg",
    "LGDisplayExtension_4QksDd6Twe.png": "oersted_experiment.png",
    # Concept
    "LGDisplayExtension_7UEwvXBegJ.png": "magnet_lines_compass.png",
    # Basic Quiz 1
    "막대자석 문제.png": "magnet_quiz_1.png",
    # Experiments
    "LGDisplayExtension_r681yHPJNP직선.png": "exp_straight_wire.png",
    "LGDisplayExtension_cU54B9ibwp원형.png": "exp_circular_wire.png",
    "LGDisplayExtension_w3NvZAdYL2솔.png": "exp_solenoid.png",
    # Basic Quiz 2
    "예제 문제 그림.png": "basic_quiz_2.png",
    # Theory
    "LGDisplayExtension_hJScqL0q2q.png": "ampere_law_overview.png",
    "LGDisplayExtension_8u29lUSHQC.png": "right_hand_rule_straight.png",
    "LGDisplayExtension_n1x26TXV02.png": "circular_wire_center.png",
    "LGDisplayExtension_Q9k6rW0A72.png": "circular_wire_pattern.png",
    "LGDisplayExtension_CAwdzkkY8C.png": "solenoid_direction.png",
    "LGDisplayExtension_LYgZWjDXWo.png": "solenoid_iron_filings.png",
    # Example & Suneung
    "예제그림1.png": "example_quiz_1.png",
    "수능문제그림.png": "suneung_quiz_fig.png",
    "수능 해설.png": "suneung_quiz_solution.png",
    # Essay
    "전동기.png": "motor_structure.png",
    "LGDisplayExtension_Ab7JBG34Ft.png": "force_on_wire.png",
}
# -----------------

def rename_image_files_and_update_code():
    print("--- 1. 이미지 파일명 변경 시작 ---")
    renamed_count = 0
    # 이미지 폴더 내 파일들 순회
    for old_name in os.listdir(image_folder):
        if old_name in rename_map:
            new_name = rename_map[old_name]
            old_path = os.path.join(image_folder, old_name)
            new_path = os.path.join(image_folder, new_name)
            
            if os.path.exists(old_path):
                os.rename(old_path, new_path)
                print(f"'{old_name}' -> '{new_name}'으로 변경 완료.")
                renamed_count += 1
            else:
                print(f"경고: '{old_name}' 파일이 이미 없거나 이름이 변경되었습니다.")

    if renamed_count == 0:
        print("변경할 파일이 없습니다. 이미 작업이 완료되었을 수 있습니다.")
    print(f"--- 총 {renamed_count}개의 파일명 변경 완료 ---\n")

    print(f"--- 2. '{app_file}' 코드 내 경로 수정 시작 ---")
    try:
        with open(app_file, 'r', encoding='utf-8') as f:
            content = f.read()
            original_content = content

        # 변환 규칙에 따라 코드 내 경로 수정
        for old_name, new_name in rename_map.items():
            old_path_in_code = f"image/{old_name}"
            new_path_in_code = f"image/{new_name}"
            content = content.replace(old_path_in_code, new_path_in_code)

        if content != original_content:
            with open(app_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"'{app_file}' 내의 이미지 경로를 모두 영어로 수정했습니다.")
        else:
            print("코드에서 수정할 경로를 찾지 못했습니다.")

        print("--- 모든 작업 완료 ---")
        
    except FileNotFoundError:
        print(f"오류: '{app_file}' 파일을 찾을 수 없습니다. 스크립트와 같은 위치에 있는지 확인하세요.")
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    rename_image_files_and_update_code()