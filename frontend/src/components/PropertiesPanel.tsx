import { Node, Member, StructuralModel } from '../types/model'

interface PropertiesPanelProps {
  model: StructuralModel
  selectedNode: Node | null
  selectedMember: Member | null
  onUpdateNode: (id: string, updates: Partial<Node>) => void
  onUpdateMember: (id: string, updates: Partial<Member>) => void
}

export default function PropertiesPanel({
  model,
  selectedNode,
  selectedMember,
  onUpdateNode,
  onUpdateMember,
}: PropertiesPanelProps) {
  // Calculate total length of all members
  const totalLength = model.members.reduce((sum, member) => {
    const startNode = model.nodes.find((n) => n.id === member.startNodeId)
    const endNode = model.nodes.find((n) => n.id === member.endNodeId)
    if (startNode && endNode) {
      const dx = endNode.x - startNode.x
      const dy = endNode.y - startNode.y
      return sum + Math.sqrt(dx * dx + dy * dy)
    }
    return sum
  }, 0)

  // Calculate member length
  const getMemberLength = (member: Member): number => {
    const startNode = model.nodes.find((n) => n.id === member.startNodeId)
    const endNode = model.nodes.find((n) => n.id === member.endNodeId)
    if (startNode && endNode) {
      const dx = endNode.x - startNode.x
      const dy = endNode.y - startNode.y
      return Math.sqrt(dx * dx + dy * dy)
    }
    return 0
  }

  return (
    <div className="w-80 bg-white border-l shadow-lg overflow-y-auto">
      <div className="p-4">
        <h2 className="text-xl font-bold mb-4">Properties</h2>

        {/* Node Properties */}
        {selectedNode && (
          <div className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded p-3">
              <h3 className="font-semibold text-blue-900 mb-2">
                Node {selectedNode.id}
              </h3>
            </div>

            <div>
              <label htmlFor="node-x" className="block text-sm font-semibold text-gray-700 mb-1">
                X Coordinate
              </label>
              <input
                id="node-x"
                type="number"
                step="0.1"
                value={selectedNode.x}
                onChange={(e) =>
                  onUpdateNode(selectedNode.id, { x: parseFloat(e.target.value) || 0 })
                }
                className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label htmlFor="node-y" className="block text-sm font-semibold text-gray-700 mb-1">
                Y Coordinate
              </label>
              <input
                id="node-y"
                type="number"
                step="0.1"
                value={selectedNode.y}
                onChange={(e) =>
                  onUpdateNode(selectedNode.id, { y: parseFloat(e.target.value) || 0 })
                }
                className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label htmlFor="node-support" className="block text-sm font-semibold text-gray-700 mb-1">
                Support Type
              </label>
              <select
                id="node-support"
                value={selectedNode.support || 'none'}
                onChange={(e) =>
                  onUpdateNode(selectedNode.id, {
                    support: e.target.value as 'pin' | 'roller' | 'fixed' | 'none',
                  })
                }
                className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="none">None</option>
                <option value="pin">Pin</option>
                <option value="roller">Roller</option>
                <option value="fixed">Fixed</option>
              </select>
            </div>

            <div className="border-t pt-4">
              <h4 className="text-sm font-semibold text-gray-700 mb-2">Applied Loads</h4>
              <div className="space-y-2">
                <div>
                  <label htmlFor="node-fx" className="block text-xs text-gray-600 mb-1">
                    Fx (kips)
                  </label>
                  <input
                    id="node-fx"
                    type="number"
                    step="0.1"
                    value={selectedNode.loads?.fx || 0}
                    onChange={(e) =>
                      onUpdateNode(selectedNode.id, {
                        loads: {
                          fx: parseFloat(e.target.value) || 0,
                          fy: selectedNode.loads?.fy || 0,
                        },
                      })
                    }
                    className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label htmlFor="node-fy" className="block text-xs text-gray-600 mb-1">
                    Fy (kips)
                  </label>
                  <input
                    id="node-fy"
                    type="number"
                    step="0.1"
                    value={selectedNode.loads?.fy || 0}
                    onChange={(e) =>
                      onUpdateNode(selectedNode.id, {
                        loads: {
                          fx: selectedNode.loads?.fx || 0,
                          fy: parseFloat(e.target.value) || 0,
                        },
                      })
                    }
                    className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Member Properties */}
        {selectedMember && (
          <div className="space-y-4">
            <div className="bg-green-50 border border-green-200 rounded p-3">
              <h3 className="font-semibold text-green-900 mb-2">
                Member {selectedMember.id}
              </h3>
            </div>

            <div className="bg-gray-50 rounded p-3">
              <div className="text-sm space-y-1">
                <div className="flex justify-between">
                  <span className="text-gray-600">Start Node:</span>
                  <span className="font-semibold">{selectedMember.startNodeId}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">End Node:</span>
                  <span className="font-semibold">{selectedMember.endNodeId}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Length:</span>
                  <span className="font-semibold">
                    {getMemberLength(selectedMember).toFixed(2)} ft
                  </span>
                </div>
              </div>
            </div>

            <div>
              <label htmlFor="member-material" className="block text-sm font-semibold text-gray-700 mb-1">
                Material
              </label>
              <select
                id="member-material"
                value={selectedMember.material}
                onChange={(e) =>
                  onUpdateMember(selectedMember.id, { material: e.target.value })
                }
                className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="steel">Steel</option>
                <option value="aluminum">Aluminum</option>
                <option value="wood">Wood</option>
              </select>
            </div>

            <div className="bg-gray-50 rounded p-3">
              <h4 className="text-sm font-semibold text-gray-700 mb-2">
                Cross-Section
              </h4>
              <p className="text-xs text-gray-600">
                {selectedMember.material === 'steel' && 'W8x24 (typical)'}
                {selectedMember.material === 'aluminum' && '6061-T6 (typical)'}
                {selectedMember.material === 'wood' && '2x6 Douglas Fir (typical)'}
              </p>
            </div>
          </div>
        )}

        {/* Model Stats (when nothing selected) */}
        {!selectedNode && !selectedMember && (
          <div className="space-y-4">
            <div className="bg-gray-50 border border-gray-200 rounded p-3">
              <h3 className="font-semibold text-gray-900 mb-3">Model Summary</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Nodes:</span>
                  <span className="font-semibold text-gray-900">
                    {model.nodes.length}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Members:</span>
                  <span className="font-semibold text-gray-900">
                    {model.members.length}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Length:</span>
                  <span className="font-semibold text-gray-900">
                    {totalLength.toFixed(2)} ft
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Supports:</span>
                  <span className="font-semibold text-gray-900">
                    {model.nodes.filter((n) => n.support && n.support !== 'none').length}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Loaded Nodes:</span>
                  <span className="font-semibold text-gray-900">
                    {
                      model.nodes.filter(
                        (n) => n.loads && (n.loads.fx !== 0 || n.loads.fy !== 0)
                      ).length
                    }
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded p-3">
              <p className="text-sm text-blue-700">
                💡 Select a node or member to view and edit its properties.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
