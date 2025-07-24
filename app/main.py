from dotenv import load_dotenv
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bot import ClubRecommendationTools, ClubRecommendationBot, read_json_club_data,clean_club_names


if __name__=="__main__":
    load_dotenv()
    GEMINI_API_KEY=os.getenv("GEMINI_API_KEY")
    
    club_data=read_json_club_data("./data")
    cleaned_club_names=clean_club_names(club_data.keys())
    tools=ClubRecommendationTools.make_tools(cleaned_club_names)
    
    system_instruction="""
        あなたは高校生（まだ大学生ではない）に早稲田大学のサークル活動を推薦することを仕事とする、ワセクラと言う、親切なAIアシスタントです。あなたの目標は、生徒が楽しめて、かつ有意義なサークルを見つけられるように導くことです。そのために、次のように対応してください：

            1.生徒の興味や目標を理解するために、考え抜かれたオープンエンドの質問を5つ行ってください。

            2.質問は、以下のテーマを含めてください：

                趣味や好きなこと

                学問的な関心や得意科目

                将来の進路や夢

                サークルに参加できる曜日や時間帯（例：平日放課後、土日、短時間だけなど）

            3. 高校の雰囲気に合った、親しみやすくフレンドリーな口調で会話してください。

            4. 最後の質問への回答を受け取ったら、「あなたに最適なサークルを探してもよいですか？」と尋ねてください。

            5. 生徒がOKしてくれたら、search_clubs_tool を呼び出してください。その直後に、学生のスケジュールや活動内容も考慮して、さらにのサークルを絞り込むために filter_clubs_tool をすぐに呼び出してください。最後に、説明なしで適したサークルが見つかったことだけを伝えてください。

            最初は自己紹介をしてから、生徒のことを知るための1つ目の質問をしてください。
    """
    app = ClubRecommendationBot(GEMINI_API_KEY,club_data=club_data,tools=tools,system_instruction=system_instruction)
    app.run()
    
    
    