// Google Apps Script 修復檔案
// 請將此函數添加到您的 Google Apps Script 專案中

function addOrUpdateSchedulesLinkBulk_(data) {
  try {
    console.log('開始批量處理行事曆資料:', data);
    
    // 檢查資料格式
    if (!data || !data.items || !Array.isArray(data.items)) {
      return {
        success: false,
        message: '資料格式錯誤：缺少 items 陣列'
      };
    }
    
    const items = data.items;
    console.log(`準備處理 ${items.length} 個行事曆項目`);
    
    // 這裡需要根據您的 Google Sheet 結構來調整
    // 假設您有一個名為 "行事曆" 的工作表
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('行事曆');
    
    if (!sheet) {
      return {
        success: false,
        message: '找不到名為 "行事曆" 的工作表'
      };
    }
    
    let inserted = 0;
    let updated = 0;
    
    // 處理每個行事曆項目
    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      
      try {
        // 檢查必要欄位
        if (!item.week || !item.time || !item.course || !item.teacher) {
          console.log(`跳過項目 ${i + 1}：缺少必要欄位`, item);
          continue;
        }
        
        // 這裡可以添加您的業務邏輯
        // 例如：檢查是否已存在相同的項目，如果存在則更新，否則新增
        
        // 簡單的示例：直接新增到工作表
        const rowData = [
          item.week,
          item.period || '',
          item.time,
          item.course,
          item.note1 || '',
          item.note2 || '',
          item.teacher,
          new Date() // 時間戳
        ];
        
        sheet.appendRow(rowData);
        inserted++;
        
        console.log(`已新增項目 ${i + 1}: ${item.course} - ${item.teacher}`);
        
      } catch (itemError) {
        console.error(`處理項目 ${i + 1} 失敗:`, itemError);
        continue;
      }
    }
    
    console.log(`批量處理完成：新增 ${inserted} 個，更新 ${updated} 個`);
    
    return {
      success: true,
      message: '批量處理成功',
      inserted: inserted,
      updated: updated,
      total: items.length
    };
    
  } catch (error) {
    console.error('批量處理失敗:', error);
    return {
      success: false,
      message: `批量處理失敗: ${error.message}`
    };
  }
}

// 如果您需要更複雜的邏輯，可以使用這個版本
function addOrUpdateSchedulesLinkBulkAdvanced_(data) {
  try {
    console.log('開始高級批量處理行事曆資料:', data);
    
    if (!data || !data.items || !Array.isArray(data.items)) {
      return {
        success: false,
        message: '資料格式錯誤：缺少 items 陣列'
      };
    }
    
    const items = data.items;
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('行事曆');
    
    if (!sheet) {
      return {
        success: false,
        message: '找不到名為 "行事曆" 的工作表'
      };
    }
    
    // 取得現有資料用於比對
    const existingData = sheet.getDataRange().getValues();
    const headers = existingData[0];
    
    // 找到關鍵欄位的索引
    const weekIndex = headers.indexOf('週次') || headers.indexOf('week');
    const timeIndex = headers.indexOf('時間') || headers.indexOf('time');
    const courseIndex = headers.indexOf('課程') || headers.indexOf('course');
    const teacherIndex = headers.indexOf('老師') || headers.indexOf('teacher');
    
    let inserted = 0;
    let updated = 0;
    
    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      
      try {
        // 檢查是否已存在相同的項目
        let existingRowIndex = -1;
        
        for (let j = 1; j < existingData.length; j++) {
          const row = existingData[j];
          if (row[weekIndex] === item.week && 
              row[timeIndex] === item.time && 
              row[courseIndex] === item.course && 
              row[teacherIndex] === item.teacher) {
            existingRowIndex = j + 1; // +1 因為工作表索引從1開始
            break;
          }
        }
        
        const rowData = [
          item.week,
          item.period || '',
          item.time,
          item.course,
          item.note1 || '',
          item.note2 || '',
          item.teacher,
          new Date()
        ];
        
        if (existingRowIndex > 0) {
          // 更新現有項目
          sheet.getRange(existingRowIndex, 1, 1, rowData.length).setValues([rowData]);
          updated++;
          console.log(`已更新項目 ${i + 1}: ${item.course} - ${item.teacher}`);
        } else {
          // 新增新項目
          sheet.appendRow(rowData);
          inserted++;
          console.log(`已新增項目 ${i + 1}: ${item.course} - ${item.teacher}`);
        }
        
      } catch (itemError) {
        console.error(`處理項目 ${i + 1} 失敗:`, itemError);
        continue;
      }
    }
    
    return {
      success: true,
      message: '高級批量處理成功',
      inserted: inserted,
      updated: updated,
      total: items.length
    };
    
  } catch (error) {
    console.error('高級批量處理失敗:', error);
    return {
      success: false,
      message: `高級批量處理失敗: ${error.message}`
    };
  }
}

