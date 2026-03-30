'use client'
import Link from 'next/link'
import { getLanguage, type Language } from '@/lib/i18n'
import { useState, useEffect } from 'react'

const FL: Record<string, { en: string; ar: string }> = {
  simulation: { en: 'Simulation', ar: 'المحاكاة' },
  architecture: { en: 'Architecture', ar: 'البنية' },
  scenarios: { en: 'Scenarios', ar: 'السيناريوهات' },
  about: { en: 'About', ar: 'حول' },
  rights: { en: 'Deevo Analytics', ar: 'ديفو أناليتكس' },
}

export default function Footer() {
  const [lang, setLang] = useState<Language>('ar')
  useEffect(() => { setLang(getLanguage()) }, [])
  const currentYear = new Date().getFullYear()
  const t = (k: string) => FL[k]?.[lang] || k

  return (
    <footer className="border-t border-ds-border bg-ds-bg" dir={lang === 'ar' ? 'rtl' : 'ltr'}>
      <div className="ds-container py-16">
        <div className="flex flex-col md:flex-row items-center justify-between gap-8">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-ds bg-ds-accent/12 border border-ds-accent/20 flex items-center justify-center">
              <span className="text-ds-accent font-bold text-xs">DS</span>
            </div>
            <span className="text-ds-text font-semibold tracking-tight">{lang === 'ar' ? 'ديفو سيم' : 'Deevo Sim'}</span>
          </div>
          <nav className="flex items-center gap-8 text-[13px] text-ds-text-secondary">
            <Link href="/demo" className="hover:text-ds-text transition-colors duration-200">{t('simulation')}</Link>
            <Link href="/architecture" className="hover:text-ds-text transition-colors duration-200">{t('architecture')}</Link>
            <Link href="/scenarios" className="hover:text-ds-text transition-colors duration-200">{t('scenarios')}</Link>
            <Link href="/#about" className="hover:text-ds-text transition-colors duration-200">{t('about')}</Link>
          </nav>
          <p className="text-micro text-ds-text-dim">
            &copy; {currentYear} {t('rights')}
          </p>
        </div>
      </div>
    </footer>
  )
}
