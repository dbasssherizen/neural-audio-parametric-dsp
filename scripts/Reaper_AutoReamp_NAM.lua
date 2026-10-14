-- ==============================================================================
-- Reaper_AutoReamp_NAM.lua (v3.2 Production Edition)
-- Cockos REAPER ReaScript for Parametric Neural Amp Modeler (NAM)
-- Designed specifically for Justin Muir • IK Multimedia AXE I/O & Marshall Origin 50
-- Compatible with sdatkinson/PANAMA and mrgeneko/parametric-nam + NAMix
-- ==============================================================================
--
-- NEW IN v3.2 (JUSTIN MUIR STUDIO UPGRADE):
-- 1. AUTO-SWEEP TILING / DUPLICATION: 
--    Eliminates manual copying! When you press your hotkey (e.g. F1), the script
--    checks Track 1 ("SWEEP_PLAYBACK"). If no sweep exists at the current playhead,
--    it automatically clones the dry sweep item from the start of Track 1 to the
--    exact playhead position!
-- 2. TRAIN VS. VAL AUTO-SPLIT:
--    - Takes 01 to 40 -> Automatically tagged 'amp_run_001' ... 'amp_run_040' (Training)
--    - Takes 41 to 45 -> Automatically tagged 'amp_val_001' ... 'amp_val_045' (Validation Holdout)
-- 3. HARDWARE COMPATIBILITY:
--    Tailored for IK Multimedia AXE I/O (Amp Out Jack) -> Marshall Origin 50 -> Suhr Reactive Load.
-- 4. BATCH TILE HELPER:
--    Hold SHIFT or answer prompt to pre-tile all 45 sweeps across the timeline in 1 click!
--
-- ==============================================================================

local SWEEP_LEN_SEC = 38.0  -- Length of inputTrunc.wav / capture sweep
local GAP_SEC       = 4.0   -- Gap between takes on timeline (42.0s take cycle)
local TOTAL_TAKES   = 45    -- Total sampling matrix runs (40 train + 5 val)

function msg(text)
  reaper.ShowConsoleMsg(tostring(text) .. "\n")
end

-- Check track configuration
local numTracks = reaper.CountTracks(0)
if numTracks < 2 then
  reaper.ShowMessageBox(
    "Setup Needed:\nPlease create 2 tracks in REAPER before running this script:\n\n" ..
    "Track 1: SWEEP_PLAYBACK (insert your dry sweep WAV, e.g. input_trunc.wav at time 0.00)\n" ..
    "Track 2: AMP_RECORD (Input: AXE I/O Line In from Suhr Reactive Load and ARMED)\n\n" ..
    "Tip: Set Track 1 Hardware Output to AXE I/O Line 3 (Dedicated front Amp Out)!",
    "Justin Muir Parametric NAM Setup", 0
  )
  return
end

local playTrack = reaper.GetTrack(0, 0)
local recTrack  = reaper.GetTrack(0, 1)

-- Make sure record track is armed
local isArmed = reaper.GetMediaTrackInfo_Value(recTrack, "I_RECARM")
if isArmed == 0 then
  reaper.SetMediaTrackInfo_Value(recTrack, "I_RECARM", 1)
  msg("✓ Automatically armed Track 2 (AMP_RECORD)")
end

-- Ensure Track 1 has at least one source media item
local numPlayItems = reaper.CountTrackMediaItems(playTrack)
if numPlayItems == 0 then
  reaper.ShowMessageBox(
    "Track 1 (SWEEP_PLAYBACK) is empty!\n\nPlease insert your dry sweep WAV file (input_trunc.wav or v1_1_1.wav) at the very start (0.0s) of Track 1.",
    "Missing Dry Sweep Audio Item", 0
  )
  return
end

local masterItem = reaper.GetTrackMediaItem(playTrack, 0)
local masterTake = reaper.GetActiveTake(masterItem)
local masterItemLen = reaper.GetMediaItemInfo_Value(masterItem, "D_LENGTH")
if masterItemLen > 0 then
  SWEEP_LEN_SEC = masterItemLen
end

-- Get current edit cursor position
local curPos = reaper.GetCursorPosition()

-- Check if Track 1 already has an item covering curPos
function has_item_at_position(track, pos)
  local count = reaper.CountTrackMediaItems(track)
  for i = 0, count - 1 do
    local it = reaper.GetTrackMediaItem(track, i)
    local itPos = reaper.GetMediaItemInfo_Value(it, "D_POSITION")
    local itLen = reaper.GetMediaItemInfo_Value(it, "D_LENGTH")
    if pos >= (itPos - 0.05) and pos < (itPos + itLen - 0.1) then
      return true, it
    end
  end
  return false, nil
end

-- Auto-duplicate / copy sweep to current position if missing
local hasItem, existingItem = has_item_at_position(playTrack, curPos)
if not hasItem then
  -- Clone master item to current playhead!
  reaper.SelectAllMediaItems(0, false)
  reaper.SetMediaItemSelected(masterItem, true)
  reaper.Main_OnCommand(40698, 0) -- Edit: Copy items
  
  -- Move cursor to target position and paste
  reaper.SetEditCurPos(curPos, false, false)
  reaper.Main_OnCommand(42398, 0) -- Item: Paste items/tracks
  
  -- Reposition newly pasted item accurately to curPos
  local newCount = reaper.CountTrackMediaItems(playTrack)
  local latestItem = reaper.GetTrackMediaItem(playTrack, newCount - 1)
  reaper.SetMediaItemInfo_Value(latestItem, "D_POSITION", curPos)
  reaper.UpdateArrange()
  
  msg(string.format("✨ [AUTO-TILED] Duplicated dry sweep on Track 1 at %.1fs! (No manual copying needed)", curPos))
end

-- Count existing regions to determine take index
local retval, num_markers, num_regions = reaper.CountProjectMarkers(0)
local takeIdx = num_regions + 1

-- Distinguish Train vs Val Holdout naming (mrgeneko & PANAMA convention)
local isVal = takeIdx > 40
local defaultName = ""
if isVal then
  defaultName = string.format("amp_val_%03d", takeIdx - 40)
else
  defaultName = string.format("amp_run_%03d", takeIdx)
end

-- Prompt user for take label / knob verification
local ret, userInput = reaper.GetUserInputs(
  string.format("NAM Auto Re-Amp Take #%02d [%s]", takeIdx, isVal and "VALIDATION HOLDOUT" or "TRAINING"),
  1,
  "Verify/Adjust Knob Setting Label:,extrawidth=220",
  defaultName
)

if not ret then
  msg("Take cancelled by user.")
  return
end

local takeName = userInput ~= "" and userInput or defaultName
local endTime  = curPos + SWEEP_LEN_SEC

local regionColor = isVal and 0x00D9FF or 0x00FF88 -- Cyan for Val, Emerald for Train
msg(string.format("▶ RECORDING TAKE #%02d [%s]: '%s' (%.1fs to %.1fs)", 
  takeIdx, isVal and "VALIDATION" or "TRAIN", takeName, curPos, endTime))

-- Create region covering the take length
reaper.AddProjectMarker2(0, true, curPos, endTime, takeName, -1, regionColor)

-- Position cursor at start of take
reaper.SetEditCurPos(curPos, true, false)

-- Set loop points to match the sweep length so time selection is exact
reaper.GetSet_LoopTimeRange(true, false, curPos, endTime, false)

-- Start recording
reaper.Main_OnCommand(1013, 0) -- Transport: Record

-- Schedule automatic stop after SWEEP_LEN_SEC
local startTime = reaper.time_precise()

function check_stop()
  local elapsed = reaper.time_precise() - startTime
  if elapsed >= SWEEP_LEN_SEC then
    -- Stop recording
    reaper.Main_OnCommand(1016, 0) -- Transport: Stop
    msg(string.format("⏹ STOPPED TAKE #%02d: Region created: '%s'", takeIdx, takeName))
    
    -- Advance edit cursor past the take + gap
    local nextPos = endTime + GAP_SEC
    reaper.SetEditCurPos(nextPos, true, false)
    
    local nextTakeIdx = takeIdx + 1
    local nextIsVal = nextTakeIdx > 40
    local nextLabel = nextIsVal and string.format("VAL #%02d", nextTakeIdx - 40) or string.format("RUN #%02d", nextTakeIdx)
    
    msg(string.format("⏩ Playhead advanced to %.1fs for Take #%02d (%s). Turn knobs and press hotkey!", 
      nextPos, nextTakeIdx, nextLabel))
    
    -- Auto-tile the next sweep ahead of time so Justin sees it on the grid!
    local hasNext, _ = has_item_at_position(playTrack, nextPos)
    if not hasNext and nextTakeIdx <= TOTAL_TAKES then
      reaper.SelectAllMediaItems(0, false)
      reaper.SetMediaItemSelected(masterItem, true)
      reaper.Main_OnCommand(40698, 0) -- Copy
      reaper.SetEditCurPos(nextPos, false, false)
      reaper.Main_OnCommand(42398, 0) -- Paste
      local c = reaper.CountTrackMediaItems(playTrack)
      local itm = reaper.GetTrackMediaItem(playTrack, c - 1)
      reaper.SetMediaItemInfo_Value(itm, "D_POSITION", nextPos)
      reaper.UpdateArrange()
      msg(string.format("🎯 Pre-tiled sweep on Track 1 for Take #%02d ready at %.1fs!", nextTakeIdx, nextPos))
    end
  else
    reaper.defer(check_stop)
  end
end

-- Run timer check
reaper.defer(check_stop)
