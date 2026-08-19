"use client"

import Link from "next/link"
import { useCallback, useEffect, useMemo, useState } from "react"
import { ArrowLeft, Users, MessageSquare, BarChart3, Plus, Loader2, RefreshCw } from "lucide-react"

interface PilotUser {
  id: string
  username: string
  display_name: string
  role: string
  organization: string | null
  created_at: string
  last_active_at: string | null
}

interface PilotSession {
  id: string
  user_id: string
  thread_id: string
  started_at: string
  ended_at: string | null
  message_count: number
  topics: string | null
  satisfaction_score: number | null
}

interface PilotSummary {
  total_users: number
  total_sessions: number
  total_messages: number
  total_feedback: number
  avg_satisfaction: number | null
  role_distribution: Record<string, number>
}

interface UserStats {
  user_id: string
  session_count: number
  total_messages: number
  feedback_count: number
  avg_satisfaction: number | null
}

const roleLabels: Record<string, string> = {
  teacher: "教师",
  extension_worker: "农技员",
  farmer: "农户",
}

const roleColors: Record<string, string> = {
  teacher: "bg-blue-100 text-blue-800",
  extension_worker: "bg-green-100 text-green-800",
  farmer: "bg-amber-100 text-amber-800",
}

export default function PilotPage() {
  const [users, setUsers] = useState<PilotUser[]>([])
  const [summary, setSummary] = useState<PilotSummary | null>(null)
  const [selectedUser, setSelectedUser] = useState<PilotUser | null>(null)
  const [userStats, setUserStats] = useState<UserStats | null>(null)
  const [busy, setBusy] = useState(true)
  const [notice, setNotice] = useState("")
  const [showAddUser, setShowAddUser] = useState(false)
  const [newUser, setNewUser] = useState({
    username: "",
    display_name: "",
    role: "teacher",
    organization: "",
    phone: "",
    email: "",
  })

  const loadUsers = useCallback(async () => {
    try {
      const response = await fetch("/api/pilot/users")
      if (!response.ok) throw new Error("无法读取用户列表")
      const payload = await response.json()
      setUsers(payload.users)
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "读取用户列表失败")
    }
  }, [])

  const loadSummary = useCallback(async () => {
    try {
      const response = await fetch("/api/pilot/summary")
      if (!response.ok) throw new Error("无法读取统计信息")
      const payload = await response.json()
      setSummary(payload)
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "读取统计信息失败")
    }
  }, [])

  const loadUserStats = useCallback(async (userId: string) => {
    try {
      const response = await fetch(`/api/pilot/users/${userId}/stats`)
      if (!response.ok) throw new Error("无法读取用户统计")
      const payload = await response.json()
      setUserStats(payload)
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "读取用户统计失败")
    }
  }, [])

  useEffect(() => {
    const init = async () => {
      setBusy(true)
      await Promise.all([loadUsers(), loadSummary()])
      setBusy(false)
    }
    init()
  }, [loadUsers, loadSummary])

  const handleAddUser = async () => {
    if (!newUser.username || !newUser.display_name) {
      setNotice("请填写用户名和显示名称")
      return
    }

    try {
      const formData = new FormData()
      formData.append("username", newUser.username)
      formData.append("display_name", newUser.display_name)
      formData.append("role", newUser.role)
      if (newUser.organization) formData.append("organization", newUser.organization)
      if (newUser.phone) formData.append("phone", newUser.phone)
      if (newUser.email) formData.append("email", newUser.email)

      const response = await fetch("/api/pilot/users", {
        method: "POST",
        body: formData,
      })

      if (!response.ok) throw new Error("添加用户失败")

      setShowAddUser(false)
      setNewUser({ username: "", display_name: "", role: "teacher", organization: "", phone: "", email: "" })
      await loadUsers()
      await loadSummary()
      setNotice("用户添加成功")
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "添加用户失败")
    }
  }

  const handleSelectUser = async (user: PilotUser) => {
    setSelectedUser(user)
    await loadUserStats(user.id)
  }

  if (busy) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-[#f0f7f4] to-white flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-[#17613c]" />
          <p className="text-gray-600">加载中...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#f0f7f4] to-white">
      <header className="bg-white/70 backdrop-blur-xl border-b border-white/20 sticky top-0 z-30">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="p-2 rounded-xl hover:bg-black/5 transition-colors">
              <ArrowLeft className="w-5 h-5 text-gray-600" />
            </Link>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">试点管理</h1>
              <p className="text-sm text-gray-500">小规模试用用户管理与统计</p>
            </div>
          </div>
          <button
            onClick={() => setShowAddUser(true)}
            className="px-4 py-2 bg-[#17613c] text-white rounded-xl hover:bg-[#0f4a2b] transition-colors flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            添加用户
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8">
        {notice && (
          <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-xl text-blue-800">
            {notice}
            <button onClick={() => setNotice("")} className="ml-2 text-blue-600 hover:text-blue-800">
              ×
            </button>
          </div>
        )}

        {/* 统计概览 */}
        {summary && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-blue-100 rounded-xl">
                  <Users className="w-5 h-5 text-blue-600" />
                </div>
                <span className="text-sm text-gray-500">总用户数</span>
              </div>
              <p className="text-3xl font-bold text-gray-900">{summary.total_users}</p>
            </div>
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-green-100 rounded-xl">
                  <MessageSquare className="w-5 h-5 text-green-600" />
                </div>
                <span className="text-sm text-gray-500">总会话数</span>
              </div>
              <p className="text-3xl font-bold text-gray-900">{summary.total_sessions}</p>
            </div>
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-amber-100 rounded-xl">
                  <BarChart3 className="w-5 h-5 text-amber-600" />
                </div>
                <span className="text-sm text-gray-500">总消息数</span>
              </div>
              <p className="text-3xl font-bold text-gray-900">{summary.total_messages}</p>
            </div>
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-purple-100 rounded-xl">
                  <BarChart3 className="w-5 h-5 text-purple-600" />
                </div>
                <span className="text-sm text-gray-500">平均满意度</span>
              </div>
              <p className="text-3xl font-bold text-gray-900">
                {summary.avg_satisfaction ? summary.avg_satisfaction.toFixed(1) : "暂无数据"}
              </p>
            </div>
          </div>
        )}

        {/* 角色分布 */}
        {summary && (
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 mb-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">用户角色分布</h2>
            <div className="flex gap-4">
              {Object.entries(summary.role_distribution).map(([role, count]) => (
                <div key={role} className="flex items-center gap-2">
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${roleColors[role] || "bg-gray-100 text-gray-800"}`}>
                    {roleLabels[role] || role}
                  </span>
                  <span className="text-gray-600">{count} 人</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 用户列表 */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
              <div className="p-4 border-b border-gray-100 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900">试用用户</h2>
                <button onClick={loadUsers} className="p-2 hover:bg-gray-100 rounded-xl transition-colors">
                  <RefreshCw className="w-4 h-4 text-gray-500" />
                </button>
              </div>
              <div className="divide-y divide-gray-100">
                {users.length === 0 ? (
                  <div className="p-8 text-center text-gray-500">暂无试用用户</div>
                ) : (
                  users.map((user) => (
                    <div
                      key={user.id}
                      onClick={() => handleSelectUser(user)}
                      className={`p-4 cursor-pointer transition-colors ${
                        selectedUser?.id === user.id ? "bg-[#17613c]/5" : "hover:bg-gray-50"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-gray-900">{user.display_name}</span>
                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${roleColors[user.role] || "bg-gray-100 text-gray-800"}`}>
                              {roleLabels[user.role] || user.role}
                            </span>
                          </div>
                          <p className="text-sm text-gray-500 mt-1">
                            {user.organization || "未设置组织"} · {user.username}
                          </p>
                        </div>
                        <div className="text-right text-sm text-gray-500">
                          {user.last_active_at
                            ? `最后活跃: ${new Date(user.last_active_at).toLocaleDateString()}`
                            : "未活跃"}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* 用户详情 */}
          <div className="lg:col-span-1">
            {selectedUser ? (
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">用户详情</h2>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm text-gray-500">姓名</label>
                    <p className="font-medium text-gray-900">{selectedUser.display_name}</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-500">用户名</label>
                    <p className="text-gray-700">{selectedUser.username}</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-500">角色</label>
                    <p className="text-gray-700">{roleLabels[selectedUser.role] || selectedUser.role}</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-500">组织</label>
                    <p className="text-gray-700">{selectedUser.organization || "未设置"}</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-500">注册时间</label>
                    <p className="text-gray-700">{new Date(selectedUser.created_at).toLocaleDateString()}</p>
                  </div>
                </div>

                {userStats && (
                  <div className="mt-6 pt-6 border-t border-gray-100">
                    <h3 className="font-medium text-gray-900 mb-3">使用统计</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-gray-500">会话数</p>
                        <p className="text-xl font-bold text-gray-900">{userStats.session_count}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">消息数</p>
                        <p className="text-xl font-bold text-gray-900">{userStats.total_messages}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">反馈数</p>
                        <p className="text-xl font-bold text-gray-900">{userStats.feedback_count}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">平均满意度</p>
                        <p className="text-xl font-bold text-gray-900">
                          {userStats.avg_satisfaction ? userStats.avg_satisfaction.toFixed(1) : "暂无"}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 text-center text-gray-500">
                选择用户查看详情
              </div>
            )}
          </div>
        </div>
      </main>

      {/* 添加用户模态框 */}
      {showAddUser && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl w-full max-w-md p-6 shadow-xl">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">添加试用用户</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">用户名 *</label>
                <input
                  type="text"
                  value={newUser.username}
                  onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#17613c] focus:border-transparent"
                  placeholder="例如: zhangsan"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">显示名称 *</label>
                <input
                  type="text"
                  value={newUser.display_name}
                  onChange={(e) => setNewUser({ ...newUser, display_name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#17613c] focus:border-transparent"
                  placeholder="例如: 张老师"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">角色 *</label>
                <select
                  value={newUser.role}
                  onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#17613c] focus:border-transparent"
                >
                  <option value="teacher">教师</option>
                  <option value="extension_worker">农技员</option>
                  <option value="farmer">农户</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">组织</label>
                <input
                  type="text"
                  value={newUser.organization}
                  onChange={(e) => setNewUser({ ...newUser, organization: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#17613c] focus:border-transparent"
                  placeholder="例如: 江西农业大学"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">电话</label>
                  <input
                    type="tel"
                    value={newUser.phone}
                    onChange={(e) => setNewUser({ ...newUser, phone: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#17613c] focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">邮箱</label>
                  <input
                    type="email"
                    value={newUser.email}
                    onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#17613c] focus:border-transparent"
                  />
                </div>
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowAddUser(false)}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleAddUser}
                className="flex-1 px-4 py-2 bg-[#17613c] text-white rounded-xl hover:bg-[#0f4a2b] transition-colors"
              >
                添加
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
