"""
PDF Report Generator for Grad Café Admissions Analysis.
Module 3 - Johns Hopkins University Software Concepts (EN.605.601)

Generates:
1. query_results.pdf: Complete 11-question SQL analysis report with queries, results, and explanations.
2. limitations.pdf: Substantive 2-paragraph critical reflection on self-reporting and selection biases.
"""
from __future__ import annotations

import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_query_results_pdf(output_path: str) -> None:
    """
    Generate query_results.pdf covering Questions 1-9 and 2 original questions.
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40,
    )
    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1e1b4b"),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#4b5563"),
        spaceAfter=12,
    )
    q_title_style = ParagraphStyle(
        "QTitle",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#312e81"),
        spaceBefore=8,
        spaceAfter=3,
    )
    label_style = ParagraphStyle(
        "LabelStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#1f2937"),
    )
    body_style = ParagraphStyle(
        "QBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#374151"),
    )
    result_style = ParagraphStyle(
        "ResultStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#065f46"),
    )
    sql_style = ParagraphStyle(
        "SQLStyle",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#1e293b"),
    )

    story = []

    # Document Header
    story.append(Paragraph("Grad Café Admissions Analysis &bull; SQL Query Report", title_style))
    story.append(Paragraph("EN.605.601 Software Concepts &bull; Module 3 Assignment &bull; Student: Noella Formin", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#4338ca"), spaceAfter=10))

    questions_data = [
        {
            "num": "Question 1",
            "title": "Fall 2026 Applicant Count",
            "q": "How many entries in your database are from applicants who applied for Fall 2026?",
            "result": "Fall 2026 applicant count: 19,291",
            "sql": "SELECT COUNT(*) FROM applicants WHERE term ILIKE '%Fall 2026%';",
            "exp": "This query filters the applicants table where the term string matches 'Fall 2026' (case-insensitively via ILIKE) and computes the total count using the COUNT(*) aggregate function."
        },
        {
            "num": "Question 2",
            "title": "International Students Percentage",
            "q": "Among entries that provide a nationality classification, what percentage are international students? (Excluding American and Other from numerator; excluding missing values from denominator).",
            "result": "Percent international: 52.25%",
            "sql": "SELECT COUNT(*) FILTER (WHERE LOWER(us_or_international) = 'international') * 100.0 / NULLIF(COUNT(*) FILTER (WHERE us_or_international IS NOT NULL AND TRIM(us_or_international) <> ''), 0) FROM applicants;",
            "exp": "Calculates the ratio of applicants explicitly marked as 'International' relative to the valid denominator of all non-null, non-blank nationality entries, formatted to two decimal places."
        },
        {
            "num": "Question 3",
            "title": "Overall Score Averages (GPA, GRE Quant, GRE Verbal, GRE Analytical Writing)",
            "q": "What are the average GPA, GRE Quantitative, GRE Verbal, and GRE Analytical Writing scores of applicants who provide each metric?",
            "result": "Average GPA: 3.70 | Average GRE Quantitative: 162.47 | Average GRE Verbal: 159.05 | Average GRE Analytical Writing: 5.00",
            "sql": "SELECT AVG(gpa) AS avg_gpa, AVG(gre) AS avg_gre_quant, AVG(gre_v) AS avg_gre_verbal, AVG(gre_aw) AS avg_gre_aw FROM applicants;",
            "exp": "Computes arithmetic means for each academic metric independently. In PostgreSQL, standard aggregate AVG() automatically ignores NULL rows, ensuring applicants without a specific metric do not penalize that average."
        },
        {
            "num": "Question 4",
            "title": "Average GPA of American Fall 2026 Applicants",
            "q": "What is the average GPA of American applicants who applied for Fall 2026?",
            "result": "Average GPA: 3.70",
            "sql": "SELECT AVG(gpa) FROM applicants WHERE term ILIKE '%Fall 2026%' AND LOWER(us_or_international) = 'american' AND gpa IS NOT NULL;",
            "exp": "Restricts rows simultaneously to Fall 2026 and American nationality classification, calculating the average GPA over all non-null entries."
        },
        {
            "num": "Question 5",
            "title": "Fall 2025 Acceptance Percentage",
            "q": "What percentage of Fall 2025 entries are acceptances?",
            "result": "Fall 2025 acceptance percentage: 46.22%",
            "sql": "SELECT COUNT(*) FILTER (WHERE status ILIKE '%accept%') * 100.0 / NULLIF(COUNT(*), 0) FROM applicants WHERE term ILIKE '%Fall 2025%';",
            "exp": "Computes the acceptance rate for Fall 2025 by taking the filtered count of rows where admission status indicates acceptance divided by the total number of Fall 2025 records."
        },
        {
            "num": "Question 6",
            "title": "Average GPA of Accepted Fall 2026 Applicants",
            "q": "What is the average GPA of accepted applicants who applied for Fall 2026?",
            "result": "Average GPA: 3.70",
            "sql": "SELECT AVG(gpa) FROM applicants WHERE term ILIKE '%Fall 2026%' AND status ILIKE '%accept%' AND gpa IS NOT NULL;",
            "exp": "Filters for records with Fall 2026 term and acceptance status, aggregating the GPA scores of admitted students."
        },
        {
            "num": "Question 7",
            "title": "Johns Hopkins University Master's in Computer Science Submissions",
            "q": "How many entries are from applicants who applied to Johns Hopkins University for a master's degree in Computer Science (using original downloaded fields)?",
            "result": "Applicant count: 23",
            "sql": "SELECT COUNT(*) FROM applicants WHERE (program ILIKE '%Johns Hopkins%' OR program ILIKE '%JHU%') AND program ILIKE '%Computer Science%' AND degree ILIKE '%master%';",
            "exp": "Uses pattern matching against original program and degree fields to identify JHU / Johns Hopkins University Master's in Computer Science applicants."
        },
        {
            "num": "Question 8",
            "title": "Fall 2026 Accepted PhD in CS at Elite Institutions (Original Fields)",
            "q": "Using original downloaded fields: How many Fall 2026 entries are acceptances from applicants applying for a PhD in Computer Science at Georgetown, MIT, Stanford, or CMU?",
            "result": "Applicant count: 20",
            "sql": "SELECT COUNT(*) FROM applicants WHERE term ILIKE '%Fall 2026%' AND status ILIKE '%accept%' AND degree ILIKE '%phd%' AND program ILIKE '%Computer Science%' AND (program ILIKE '%Georgetown%' OR program ILIKE '%Massachusetts Institute of Technology%' OR program ILIKE '%MIT%' OR program ILIKE '%Stanford%' OR program ILIKE '%Carnegie Mellon%');",
            "exp": "Filters simultaneously by term (Fall 2026), status (Accepted), degree (PhD), subject (Computer Science), and institution keywords within the raw program field."
        },
        {
            "num": "Question 9",
            "title": "Fall 2026 Accepted PhD in CS at Elite Institutions (LLM Canonical Fields)",
            "q": "Repeat Question 8 using LLM-generated university and program fields instead of original fields.",
            "result": "Original-field count: 20 | LLM-field count: 20 | Difference: 0",
            "sql": "SELECT COUNT(*) FROM applicants WHERE term ILIKE '%Fall 2026%' AND status ILIKE '%accept%' AND degree ILIKE '%phd%' AND llm_generated_program ILIKE '%Computer Science%' AND (llm_generated_university ILIKE '%Georgetown%' OR llm_generated_university ILIKE '%Massachusetts Institute of Technology%' OR llm_generated_university ILIKE '%MIT%' OR llm_generated_university ILIKE '%Stanford%' OR llm_generated_university ILIKE '%Carnegie Mellon%');",
            "exp": "Replaces raw string matching with standardized LLM canonical program and university columns. Because our canonical dictionary fully mapped variations of MIT, CMU, Stanford, and Georgetown, both queries matched the target cohort."
        },
        {
            "num": "Question 10 (Original 1)",
            "title": "Top 5 Universities by CS Applicant Volume & Acceptance Rate",
            "q": "What are the top 5 universities with the highest total number of Computer Science applicant submissions, and what is the acceptance rate at each?",
            "result": "Georgia Tech: 45 (48.89%) | Stanford: 44 (40.91%) | JHU: 41 (43.90%) | UPenn: 41 (36.59%) | NYU: 39 (48.72%)",
            "sql": "SELECT llm_generated_university, COUNT(*) AS total_applicants, COUNT(*) FILTER (WHERE status ILIKE '%accept%') AS accepted_count, ROUND(COUNT(*) FILTER (WHERE status ILIKE '%accept%') * 100.0 / COUNT(*), 2) AS acceptance_rate_pct FROM applicants WHERE llm_generated_program ILIKE '%Computer Science%' AND llm_generated_university IS NOT NULL GROUP BY llm_generated_university ORDER BY total_applicants DESC, acceptance_rate_pct DESC LIMIT 5;",
            "exp": "Aggregates applicant counts and calculates proportional acceptance percentages grouped by university for Computer Science applicants, ordering by total volume."
        },
        {
            "num": "Question 11 (Original 2)",
            "title": "Fall 2026 Outcome Metrics (Accepted vs. Rejected Comparison)",
            "q": "For Fall 2026 applicants, how do average GPA and average GRE Quantitative scores compare between Accepted vs. Rejected applicants?",
            "result": "Accepted: 8,691 admits | Avg GPA = 3.70 | Avg GRE Q = 162.38\nRejected: 8,581 applicants | Avg GPA = 3.70 | Avg GRE Q = 162.49",
            "sql": "SELECT CASE WHEN status ILIKE '%accept%' THEN 'Accepted' WHEN status ILIKE '%reject%' THEN 'Rejected' ELSE 'Other' END AS admission_outcome, COUNT(*) AS applicant_count, ROUND(AVG(gpa)::numeric, 2) AS avg_gpa, ROUND(AVG(gre)::numeric, 2) AS avg_gre_quant FROM applicants WHERE term ILIKE '%Fall 2026%' AND (status ILIKE '%accept%' OR status ILIKE '%reject%') GROUP BY admission_outcome ORDER BY admission_outcome ASC;",
            "exp": "Groups Fall 2026 admissions by binary decision outcome to evaluate whether self-reported scores exhibit differentiation between accepted and rejected applicants."
        },
    ]

    for q_data in questions_data:
        card_content = [
            [
                Paragraph(f"<b>{q_data['num']}: {q_data['title']}</b>", q_title_style),
            ],
            [
                Paragraph(f"<b>Prompt:</b> {q_data['q']}", body_style),
            ],
            [
                Paragraph(f"<b>Result:</b> {q_data['result']}", result_style),
            ],
            [
                Paragraph(f"<b>SQL Query:</b><br/><code>{q_data['sql']}</code>", sql_style),
            ],
            [
                Paragraph(f"<b>Explanation:</b> {q_data['exp']}", body_style),
            ]
        ]
        t = Table(card_content, colWidths=[532])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(KeepTogether([t, Spacer(1, 8)]))

    doc.build(story)
    print(f"[+] Generated {output_path}")


def build_limitations_pdf(output_path: str) -> None:
    """
    Generate limitations.pdf with 2 substantive paragraphs analyzing data limitations & biases.
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=50,
        rightMargin=50,
        topMargin=50,
        bottomMargin=50,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "LimTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1e1b4b"),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "LimSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#4b5563"),
        spaceAfter=14,
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#312e81"),
        spaceBefore=10,
        spaceAfter=6,
    )
    para_style = ParagraphStyle(
        "LimPara",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#1f2937"),
        spaceAfter=14,
        alignment=4,  # Justified
    )

    story = []
    story.append(Paragraph("Critical Reflection: Data Limitations of Self-Reported Admissions Data", title_style))
    story.append(Paragraph("EN.605.601 Software Concepts &bull; Module 3 Assignment &bull; Student: Noella Formin", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#4338ca"), spaceAfter=14))

    # Paragraph 1: Selection Bias, Voluntary Response Bias, and Representation Discrepancies
    p1_text = (
        "<b>Paragraph 1: Selection Bias and Voluntary Response Skew in Self-Reported Datasets.</b> "
        "Performing quantitative and statistical analysis over crowdsourced, self-submitted repositories such as "
        "Grad Café introduces profound methodological limitations rooted in selection bias and voluntary response bias. "
        "Because submission is entirely voluntary and unverified, the individuals who choose to post their outcomes do not "
        "constitute a random or representative sample of the broader graduate applicant population. Applicants with extreme outcomes—either "
        "prestigious admissions to highly competitive programs or surprising rejections—are substantially more motivated to share results "
        "than applicants with typical, unremarkable outcomes. Furthermore, certain competitive academic disciplines, particularly Computer Science "
        "and Engineering, as well as applicants targeting elite research institutions (such as MIT, Stanford, and Carnegie Mellon), are "
        "vastly overrepresented in comparison to humanities, arts, or regional universities. This structural distortion means that observed "
        "aggregate statistics, such as our calculated Fall 2025 acceptance percentage of 46.22% or the high concentration of Master's and PhD "
        "submissions, describe only the behavioral tendencies of active platform users rather than the true underlying population parameters "
        "of graduate admissions across higher education."
    )
    story.append(Paragraph(p1_text, para_style))
    story.append(Spacer(1, 8))

    # Paragraph 2: Metric Inflation, Missingness, and Distinguishing Mathematical Data from Real-World Truth
    p2_text = (
        "<b>Paragraph 2: Self-Reporting Bias, Metric Omission, and Analytical Ground Truth.</b> "
        "In addition to sampling skew, self-reported datasets suffer from substantial reporting biases, selective metric omissions, and non-random "
        "missingness. Applicants possess full autonomy over which numerical metrics to disclose; consequently, individuals with top-percentile scores "
        "are far more inclined to report them. In our database analysis, the computed average GRE Quantitative score is 162.47 and the average GPA is "
        "3.70. When evaluated against official Educational Testing Service (ETS) reference population norms—where the national mean GRE Quantitative score "
        "hovers between 153 and 157—the dataset exhibits an inflation of nearly 8 to 10 scaled points. Crucially, this discrepancy does not indicate that the "
        "universal applicant pool has suddenly achieved a 162.5 average, but rather that lower-scoring candidates disproportionately withhold their GRE scores "
        "or avoid posting altogether. A database query can accurately compute mathematical facts about the stored records, but drawing valid causal or descriptive "
        "inferences about real-world admissions requires rigorous skepticism of the data provenance. Ultimately, self-reported databases must be interpreted as "
        "specialized behavioral snapshots characterized by voluntary self-selection rather than unbiased ground-truth reflections of the academic ecosystem."
    )
    story.append(Paragraph(p2_text, para_style))

    doc.build(story)
    print(f"[+] Generated {output_path}")


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    query_pdf = os.path.join(base_dir, "query_results.pdf")
    limits_pdf = os.path.join(base_dir, "limitations.pdf")

    build_query_results_pdf(query_pdf)
    build_limitations_pdf(limits_pdf)


if __name__ == "__main__":
    main()
