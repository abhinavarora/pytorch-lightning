import inspect
import os

import torch
from torch.utils.data import DataLoader, Dataset

from pytorch_lightning import LightningModule, Trainer
from pytorch_lightning.loops.batch.yield_loop import YieldLoop
from pytorch_lightning.plugins import DDPPlugin


class RandomDataset(Dataset):

    def __init__(self, size, length):
        self.len = length
        self.data = torch.randn(length, size)

    def __getitem__(self, index):
        return self.data[index]

    def __len__(self):
        return self.len


class BoringModel(LightningModule):

    def __init__(self):
        super().__init__()
        self.layer1 = torch.nn.Linear(32, 32)
        self.layer2 = torch.nn.Linear(32, 32)
        self.head = torch.nn.Linear(32, 2)

    def training_step(self, batch, batch_idx, optimizer_idx=0):
        loss0 = self.head(self.layer1(batch)).sum()
        # self.log("train_loss_0", loss0)
        yield loss0

        print("yield 0")

        loss1 = self.head(self.layer2(batch)).sum()
        # self.log("train_loss_1", loss0)

        print("yield 1")

        yield loss1

    def configure_optimizers(self):
        opt1 = torch.optim.SGD(self.layer1.parameters(), lr=0.1)
        opt2 = torch.optim.SGD(self.layer2.parameters(), lr=0.1)
        return opt1, opt2


def run():
    train_data = DataLoader(RandomDataset(32, 64), batch_size=2)
    val_data = DataLoader(RandomDataset(32, 64), batch_size=2)
    test_data = DataLoader(RandomDataset(32, 64), batch_size=2)

    model = BoringModel()
    trainer = Trainer(
        default_root_dir=os.getcwd(),
        limit_train_batches=1,
        limit_val_batches=1,
        num_sanity_val_steps=0,
        max_epochs=1,
        weights_summary=None,
        # accelerator="ddp_cpu",
        # plugins=DDPPlugin(),
        # num_processes=2,
    )

    yield_batch_loop = YieldLoop()
    trainer.fit_loop.epoch_loop.connect(batch_loop=yield_batch_loop)

    trainer.fit(model, train_dataloaders=train_data, val_dataloaders=val_data)


if __name__ == '__main__':
    run()
