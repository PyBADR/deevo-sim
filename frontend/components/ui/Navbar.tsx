'use client'
import { useState, useEffect } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { Menu, X, BookOpen, Github } from 'lucide-react'

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 10)
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const navLinks = [
    { href: '/#hero', label: 'Get Started' },
    { href: '/demo', label: 'Simulation' },
    { href: '/architecture', label: 'Architecture' },
    { href: '/#about', label: 'About' },
  ]

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
        scrolled
          ? 'bg-ds-bg/70 backdrop-blur-xl border-b border-ds-border/60 shadow-ds'
          : 'bg-transparent border-b border-transparent'
      }`}
    >
      <div className="ds-container">
        <div className="flex items-center justify-between h-[72px]">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-9 h-9 rounded-ds bg-ds-accent/12 border border-ds-accent/20 flex items-center justify-center transition-all duration-300 group-hover:bg-ds-accent/18 group-hover:border-ds-accent/30 group-hover:shadow-ds-glow">
              <span className="text-ds-accent font-bold text-sm">DS</span>
            </div>
            <span className="text-ds-text font-semibold text-[17px] tracking-tight">Deevo Sim</span>
          </Link>

          <div className="hidden lg:flex items-center gap-1 bg-ds-surface/50 backdrop-blur-sm border border-ds-border/40 rounded-full px-1.5 py-1">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="px-4 py-2 text-[13px] font-medium text-ds-text-secondary hover:text-ds-text transition-all duration-200 rounded-full hover:bg-ds-card/80"
              >
                {link.label}
              </Link>
            ))}
          </div>

          <div className="hidden lg:flex items-center gap-2">
            <button className="flex items-center gap-2 px-3.5 py-2 text-[13px] font-medium text-ds-text-secondary hover:text-ds-text transition-all duration-200 rounded-ds hover:bg-ds-card/60">
              <BookOpen size={15} />
              Docs
            </button>
            <button className="flex items-center gap-2 px-3.5 py-2 text-[13px] font-medium text-ds-text-secondary hover:text-ds-text transition-all duration-200 rounded-ds hover:bg-ds-card/60">
              <Github size={15} />
              GitHub
            </button>
          </div>

          <button
            className="lg:hidden p-2.5 text-ds-text-secondary hover:text-ds-text rounded-ds hover:bg-ds-card transition-all"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>

        <AnimatePresence>
          {mobileOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.25 }}
              className="lg:hidden overflow-hidden"
            >
              <div className="pb-5 pt-3 border-t border-ds-border/50 space-y-1">
                {navLinks.map((link) => (
                  <Link
                    key={link.href}
                    href={link.href}
                    className="block px-4 py-3 text-ds-text-secondary hover:text-ds-text hover:bg-ds-card/60 rounded-ds transition-all"
                    onClick={() => setMobileOpen(false)}
                  >
                    {link.label}
                  </Link>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </nav>
  )
        }
