"use client"
import { createContext, useContext, useState } from "react"

interface SidebarContextType {
  leftOpen: boolean
  setLeftOpen: (v: boolean) => void
  rightOpen: boolean
  setRightOpen: (v: boolean) => void
}

export const SidebarContext = createContext<SidebarContextType>({
  leftOpen: true,
  setLeftOpen: () => {},
  rightOpen: true,
  setRightOpen: () => {},
})

export const useSidebar = () => useContext(SidebarContext)