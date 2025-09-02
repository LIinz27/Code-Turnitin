const fs = require('fs');
const path = require('path');

const clearDownloadsFolder = () => {
  const downloadsPath = path.join(__dirname, 'downloads');

  fs.readdir(downloadsPath, (err, files) => {
    if (err) {
      console.error('Error reading downloads folder:', err);
      return;
    }

    files.forEach((file) => {
      const filePath = path.join(downloadsPath, file);

      fs.unlink(filePath, (unlinkErr) => {
        if (unlinkErr) {
          console.error(`Error deleting ${file}:`, unlinkErr);
        } else {
          console.log(`Deleted ${file} successfully`);
        }
      });
    });
  });
};

clearDownloadsFolder();
