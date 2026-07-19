import os


def combine_markdown_files(file_matrix, names, output_dir="combined_docs"):
    """二次元リストで指定されたMarkdownファイルを結合する関数

    :param file_matrix: Markdownファイルの相対パスを含む二次元リスト (例: [['./a.md', './b.md'],
    ['./c.md']])
    :param names: 結合後のファイル名として使用される名前のリスト
    :param output_dir: 結合後のファイルを保存するディレクトリ
    """
    # 出力ディレクトリが存在しない場合は作成
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 二次元リスト L[i][j] をループ処理
    for i, file_list in enumerate(file_matrix):
        if not file_list:
            continue

        combined_content = []
        header_info = ["# 結合ファイル構成案内\n", "このファイルは以下の順序で結合されています：\n"]

        # 先頭に記載するファイル構成リストを作成
        for idx, file_path in enumerate(file_list):
            # 表示用にパスを標準化
            norm_path = os.path.normpath(file_path)
            header_info.append(f"{idx + 1}. `{norm_path}`")

        header_info.append("\n---\n")  # 区切り線
        combined_content.append("\n".join(header_info))

        # 各ファイルを走査して結合
        for j, file_path in enumerate(file_list):
            norm_path = os.path.normpath(file_path)

            # ファイルの存在確認
            if not os.path.exists(norm_path):
                print(f"警告: ファイルが見つかりません: {norm_path}")
                continue

            # ファイル変更点の区切りを挿入（最初のファイルの前には不要な場合は j > 0 とする）
            combined_content.append(
                f"\n\n\n--- \n## ファイル名: `{norm_path}`\n---\n\n"
            )
            # ファイル内容の読み込み
            with open(norm_path, "r", encoding="utf-8") as f:
                content = f.read()
                combined_content.append(content)

        # 結合した内容を書き出し
        output_filename = f"{names[i]}.md"
        output_path = os.path.join(output_dir, output_filename)

        with open(output_path, "w", encoding="utf-8") as out_f:
            out_f.write("".join(combined_content))

        print(f"結合完了: {output_path}")


# --- 使い方・設定例 ---
if __name__ == "__main__":
    # 人間が入力しやすい相対パスの二次元リスト L[i][j]
    files = [
        ["./docs/00_overview.md", "./docs/01_requirements.md", "./docs/02_architecture.md", "./docs/03_gui.md", "./docs/04_planetarium.md"],
        ["./docs/97_architecture_principles.md", "./docs/98_naming_convention.md", "./docs/99_glossary.md", "./docs/ai_development.md", "./docs/development_environment.md"],
        ["./docs/implementation/03_first_rendering.md"]
    ]

    names = ["specification", "philosophy", "implementation"]

    # 関数の実行
    combine_markdown_files(files, names)