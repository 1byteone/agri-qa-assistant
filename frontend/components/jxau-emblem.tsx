"use client"

/**
 * 江西农业大学校徽（SVG 复刻版）
 * 设计要素（依据百度百科/官网"学校标识"描述）：
 * - 圆形徽标
 * - 上方弧形排列"江西农业大学"字样
 * - 中央为麦穗 + "农"字（农业高校特征元素）
 * - 下方"1905"字样（办学源起年份：江西实业学堂）
 * - 底部边缘英文译名 JIANGXI AGRICULTURAL UNIVERSITY
 */

const GOLD = "#f5c842"
const GREEN = "#0b6b34"
const DARK_GREEN = "#084f26"

// 单束麦穗：从 (50,74) 向左上生长
function WheatStalk({ flip = false }: { flip?: boolean }) {
  return (
    <g transform={flip ? "translate(100,0) scale(-1,1)" : undefined}>
      {/* 茎 */}
      <path
        d="M 50,74 C 46,66 43,58 42,50"
        stroke={GOLD}
        strokeWidth="1.2"
        fill="none"
        strokeLinecap="round"
      />
      {/* 麦粒（沿茎分布的椭圆） */}
      <ellipse cx="47.5" cy="68" rx="3.4" ry="1.5" fill={GOLD} transform="rotate(-45 47.5 68)" />
      <ellipse cx="45.5" cy="62" rx="3.4" ry="1.5" fill={GOLD} transform="rotate(-55 45.5 62)" />
      <ellipse cx="43.8" cy="56" rx="3.4" ry="1.5" fill={GOLD} transform="rotate(-62 43.8 56)" />
      <ellipse cx="42.6" cy="50.5" rx="3.2" ry="1.5" fill={GOLD} transform="rotate(-68 42.6 50.5)" />
    </g>
  )
}

export function JXAUEmblem({ className = "w-10 h-10" }: { className?: string }) {
  return (
    <svg viewBox="0 0 100 100" className={className} role="img" aria-label="江西农业大学校徽">
      {/* 外圆徽标 */}
      <circle cx="50" cy="50" r="49" fill={GREEN} />
      <circle cx="50" cy="50" r="45.5" fill="none" stroke={GOLD} strokeWidth="1.6" />
      {/* 内圈装饰线 */}
      <circle cx="50" cy="50" r="42.5" fill="none" stroke="#ffffff" strokeOpacity="0.35" strokeWidth="0.6" strokeDasharray="1.5 1.5" />
      {/* 中央徽章底 */}
      <circle cx="50" cy="50" r="21" fill={DARK_GREEN} />
      <circle cx="50" cy="50" r="21" fill="none" stroke={GOLD} strokeWidth="0.8" />
      {/* 中央"农"字 */}
      <text
        x="50"
        y="57"
        textAnchor="middle"
        fontSize="26"
        fontWeight="700"
        fill={GOLD}
        fontFamily="STKaiti, KaiTi, serif"
      >
        农
      </text>
      {/* 麦穗（对称两束） */}
      <WheatStalk />
      <WheatStalk flip />
      {/* 顶部弧形文字：江西农业大学 */}
      <path id="jxau-top-arc" d="M 18,50 A 32,32 0 0 1 82,50" fill="none" />
      <text fontSize="8.6" fontWeight="600" fill="#ffffff" letterSpacing="2.4">
        <textPath href="#jxau-top-arc" startOffset="50%" textAnchor="middle">
          江西农业大学
        </textPath>
      </text>
      {/* 底部弧形文字：英文译名 */}
      <path id="jxau-bottom-arc" d="M 20,54 A 30,30 0 0 0 80,54" fill="none" />
      <text fontSize="3.2" fontWeight="500" fill="#ffffff" opacity="0.85" letterSpacing="1.1">
        <textPath href="#jxau-bottom-arc" startOffset="50%" textAnchor="middle">
          JIANGXI AGRICULTURAL UNIVERSITY
        </textPath>
      </text>
      {/* 年份 1905 */}
      <text x="50" y="93" textAnchor="middle" fontSize="7" fontWeight="700" fill={GOLD} letterSpacing="1">
        1905
      </text>
    </svg>
  )
}