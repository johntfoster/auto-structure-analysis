// Core structural model types

export interface Node {
  id: string
  x: number
  y: number
  support?: 'pin' | 'roller' | 'fixed' | 'none'
  loads?: { fx: number; fy: number }
}

export interface Member {
  id: string
  startNodeId: string
  endNodeId: string
  material: string
}

export interface StructuralModel {
  nodes: Node[]
  members: Member[]
}

// Editor-specific types

export type EditorMode = 
  | 'select'
  | 'add-node'
  | 'add-member'
  | 'add-load'
  | 'delete'

export type SelectionType = 'node' | 'member' | null

export interface Selection {
  type: SelectionType
  id: string | null
}

export interface ViewportTransform {
  scale: number
  offsetX: number
  offsetY: number
}

// State for model editor

export interface EditorState {
  model: StructuralModel
  selection: Selection
  mode: EditorMode
  tempMemberStart: string | null // For two-click member creation
  viewport: ViewportTransform
  history: StructuralModel[]
  historyIndex: number
}

// Actions for reducer

export type EditorAction =
  | { type: 'SET_MODE'; mode: EditorMode }
  | { type: 'SET_MODEL'; model: StructuralModel }
  | { type: 'ADD_NODE'; node: Node }
  | { type: 'UPDATE_NODE'; id: string; updates: Partial<Node> }
  | { type: 'DELETE_NODE'; id: string }
  | { type: 'ADD_MEMBER'; member: Member }
  | { type: 'UPDATE_MEMBER'; id: string; updates: Partial<Member> }
  | { type: 'DELETE_MEMBER'; id: string }
  | { type: 'SELECT'; selection: Selection }
  | { type: 'SET_TEMP_MEMBER_START'; nodeId: string | null }
  | { type: 'SET_VIEWPORT'; viewport: ViewportTransform }
  | { type: 'ZOOM_IN' }
  | { type: 'ZOOM_OUT' }
  | { type: 'FIT_TO_VIEW'; canvasWidth: number; canvasHeight: number }
  | { type: 'UNDO' }
  | { type: 'REDO' }
  | { type: 'SAVE_HISTORY' }
