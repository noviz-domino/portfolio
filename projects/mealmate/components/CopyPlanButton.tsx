'use client'

import { useState } from 'react'

// F-14 마크다운 복사. 회원·방문자 모두에게 보인다.
// 마크다운 문자열은 서버(상세 페이지)에서 미리 만들어 넘겨받는다.
// 클립보드 API는 https 또는 localhost에서만 동작하므로, 실패하면 안내 문구를 띄운다.
export function CopyPlanButton({ markdown }: { markdown: string }) {
  const [copied, setCopied] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function copy() {
    setError(null)
    try {
      await navigator.clipboard.writeText(markdown)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      setError('복사에 실패했어요. 브라우저 주소창이 https인지 확인해 주세요.')
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={copy}
        className="btn btn-secondary btn-sm"
      >
        {copied ? '복사됐어요' : '마크다운 복사'}
      </button>
      {error && <p className="w-full text-sm text-danger">{error}</p>}
    </>
  )
}
