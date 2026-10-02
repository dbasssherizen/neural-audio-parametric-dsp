-- ==============================================================================
-- Reaper_AutoReamp_NAM.lua
-- Cockos REAPER ReaScript for Parametric Neural Amp Modeler (NAM)
-- Designed for Justin Muir - 48kHz 24-bit Precision Re-Amping
-- ==============================================================================
--
-- WORKFLOW SUMMARY:
-- Eliminates manual start/stop, trimming, and naming of 45 sweeps!
-- 
-- SETUP (Takes 60 seconds):
-- 1. In REAPER: Actions -> Show action list -> New action -> Load ReaScript -> Select this file.
-- 2. Bind it to a key (e.g., F1, Space, or Numpad Enter).
-- 3. Track 1: Name "SWEEP_PLAYBACK" (insert inputTrunc.wav at time 0.00).
-- 4. Track 2: Name "AMP_RECORD" (Input: your audio interface input from loadbox/mic).
-- 5. Arm Track 2 for recording.
--
-- USAGE:
-- 1. Dial the knobs on your physical amp according to your run sheet.
-- 2. Hit your hotkey (e.g. F1).
-- 3. REAPER will:
--    - Position the playhead
--    - Start recording Track 2 while playing Track 1
--    - Automatically record for exactly 38.0 seconds
--    - Stop transport
--    - Create a labeled Region (e.g., "take_01_G6.5_B5.0_M8.5_T7.0_M3.5")
--    - Advance edit cursor by 42.0 seconds ready for the next take!
-- 4. When all takes are done:
--    - File -> Render
--    - Source: "All Project Regions"
--    - Bounds: "All regions"
--    - File name: "$region.wav"
--    - Click "Render 45 Files" -> Done in 10 seconds!
-- ==============================================================================

local SWEEP_LEN_SEC = 38.0  -- Length of inputTrunc.wav
local GAP_SEC       = 4.0   -- Gap between takes on timeline

function msg(text)
  reaper.ShowConsoleMsg(tostring(text) .. "\n")
end

-- Check track configuration
local numTracks = reaper.CountTracks(0)
if numTracks < 2 then
  reaper.ShowMessageBox(
    "Setup Needed:\nPlease create 2 tracks in REAPER before running this script:\n\n" ..
    "Track 1: SWEEP_PLAYBACK (inputTrunc.wav placed at the start)\n" ..
    "Track 2: AMP_RECORD (Set to your amp input channel and ARMED for record)",
    "Parametric NAM Setup Error", 0
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

-- Get current cursor position
local curPos = reaper.GetCursorPosition()

-- Count existing regions to determine take index
local retval, num_markers, num_regions = reaper.CountProjectMarkers(0)
local takeIdx = num_regions + 1
local defaultName = string.format("take_%02d_sweep", takeIdx)

-- Prompt user for take label (optional, prefilled with take count)
local ret, userInput = reaper.GetUserInputs(
  string.format("NAM Auto Re-Amp Take #%02d", takeIdx),
  1,
  "Enter Take Label / Knob Settings:,extrawidth=180",
  defaultName
)

if not ret then
  msg("Take cancelled.")
  return
end

local takeName = userInput ~= "" and userInput or defaultName
local endTime = curPos + SWEEP_LEN_SEC

msg(string.format("▶ RECORDING TAKE #%02d: '%s' [%.1fs to %.1fs]", takeIdx, takeName, curPos, endTime))

-- Create region covering the take length
reaper.AddProjectMarker2(0, true, curPos, endTime, takeName, -1, 0x00FF88)

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
    msg(string.format("⏹ STOPPED TAKE #%02d. Region created: '%s'", takeIdx, takeName))
    
    -- Advance edit cursor past the take + gap
    local nextPos = endTime + GAP_SEC
    reaper.SetEditCurPos(nextPos, true, false)
    msg(string.format("⏩ Playhead advanced to %.1fs for next take. Turn knobs and press hotkey!", nextPos))
  else
    reaper.defer(check_stop)
  end
end

-- Run timer check
reaper.defer(check_stop)
