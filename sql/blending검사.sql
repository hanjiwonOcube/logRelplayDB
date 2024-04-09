INSERT INTO judge (final_decision)
SELECT
    CASE
        WHEN COUNT(*) = (SELECT COUNT(*) FROM blending) THEN 'Blending detected!'  -- 모든 패턴이 일치하는 경우 'Blending detected!'으로 설정
        ELSE 'No blending detected.'
    END AS final_decision
FROM
    judgement_data AS jd
LEFT JOIN
    blending AS b ON jd.action = b.action AND jd.value = b.value;
